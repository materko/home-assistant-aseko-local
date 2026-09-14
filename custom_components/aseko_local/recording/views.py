"""HTTP side of the Aseko test cases card: photo upload, live status and zip export.

The card (``frontend/aseko-test-cases-card.js``) is loaded on every dashboard, so
``type: custom:aseko-test-cases-card`` works without adding a resource by hand.  It
talks to three authenticated endpoints, admin only like the diagnostics
download they extend:

* ``POST /api/aseko_local/photo`` -- a photo straight from the phone camera
  (multipart field ``photo``, optional ``note``).  The marker is written into
  every entry's frame log the moment the upload arrives, and the photo is
  stored under that time.
* ``GET /api/aseko_local/status`` -- how long ago each unit's last frame
  arrived, so the card can show it while waiting before a change.
* ``GET /api/aseko_local/export`` -- frames, markers, diagnostics and photos
  as one zip.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.http import KEY_HASS
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from .photos import PhotoStore, build_export_zip

_LOGGER = logging.getLogger(__name__)

STATIC_URL = f"/{DOMAIN}_static"
CARD_FILE = "aseko-test-cases-card.js"
DATA_RECORDING = f"{DOMAIN}_recording"
# Well under Home Assistant's 16 MB request limit; phone photos are 2-8 MB.
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def photo_store(hass: HomeAssistant) -> PhotoStore:
    """The one photo folder shared by every Aseko Local entry."""
    return hass.data[DATA_RECORDING]["photos"]


async def async_setup_recording(hass: HomeAssistant, version: str) -> None:
    """Serve the card, load it on every dashboard and register the endpoints, once."""
    if DATA_RECORDING in hass.data:
        return
    if hass.http is None or "frontend" not in hass.config.components:
        # A bare test instance without the web stack: nothing to serve to.
        _LOGGER.debug("HTTP or frontend not loaded; the Aseko test cases card is off")
        return
    hass.data[DATA_RECORDING] = {
        "photos": PhotoStore(Path(hass.config.path(DOMAIN, "photos"))),
    }
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                STATIC_URL, str(Path(__file__).parent / "frontend"), cache_headers=False
            )
        ]
    )
    add_extra_js_url(hass, f"{STATIC_URL}/{CARD_FILE}?v={version}")
    hass.http.register_view(AsekoPhotoView())
    hass.http.register_view(AsekoPhotoFileView())
    hass.http.register_view(AsekoForgetView())
    hass.http.register_view(AsekoStatusView())
    hass.http.register_view(AsekoExportView())


def _loaded_entries(hass: HomeAssistant) -> list[Any]:
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if getattr(entry, "runtime_data", None)
    ]


def _require_admin(request: web.Request) -> HomeAssistant:
    if not request["hass_user"].is_admin:
        raise Unauthorized
    return request.app[KEY_HASS]


class AsekoPhotoView(HomeAssistantView):
    """Store a display photo and write a marker at upload time."""

    url = f"/api/{DOMAIN}/photo"
    name = f"api:{DOMAIN}:photo"

    async def post(self, request: web.Request) -> web.Response:
        hass = _require_admin(request)
        received = dt_util.utcnow()
        entries = _loaded_entries(hass)
        if not entries:
            return self.json_message("No Aseko Local entry is loaded", 409)

        note: str | None = None
        data = b""
        reader = await request.multipart()
        while (part := await reader.next()) is not None:
            if part.name == "note":
                note = (await part.text()).strip()[:200] or None
            elif part.name == "photo":
                data = await part.read(decode=False)
                if len(data) > MAX_UPLOAD_BYTES:
                    return self.json_message("Photo too large", 413)
        if not data:
            return self.json_message("No photo in the upload", 400)

        saved = await hass.async_add_executor_job(
            photo_store(hass).save, data, received, note
        )
        markers = []
        for entry in entries:
            marker = entry.runtime_data.coordinator.mark_dump(
                note, {"photo": saved.file, "captured": saved.captured}
            )
            markers.append(
                {
                    "entry": entry.title,
                    "marker": marker["marker"],
                    "time": dt_util.as_local(marker["time"]).isoformat(),
                    "seconds_since_last_frame": marker["seconds_since_last_frame"],
                }
            )
        _LOGGER.info("Aseko display photo %s stored with %s", saved.file, markers)
        return self.json(
            {"photo": saved.file, "bytes": saved.bytes, "markers": markers}
        )


class AsekoPhotoFileView(HomeAssistantView):
    """One stored photo, for the card's case list."""

    url = f"/api/{DOMAIN}/photo/{{name}}"
    name = f"api:{DOMAIN}:photo_file"

    async def get(self, request: web.Request, name: str) -> web.StreamResponse:
        hass = _require_admin(request)
        store = photo_store(hass)
        if "/" in name or "\\" in name or name.startswith("."):
            return self.json_message("Bad photo name", 400)
        path = store.directory / name
        if not await hass.async_add_executor_job(path.is_file):
            return self.json_message("No such photo", 404)
        return web.FileResponse(path)


class AsekoForgetView(HomeAssistantView):
    """Clear the list of cases (frames and photos stay)."""

    url = f"/api/{DOMAIN}/forget"
    name = f"api:{DOMAIN}:forget"

    async def post(self, request: web.Request) -> web.Response:
        hass = _require_admin(request)
        for entry in _loaded_entries(hass):
            entry.runtime_data.coordinator.forget_markers()
        return self.json({"ok": True})


class AsekoStatusView(HomeAssistantView):
    """How long ago each unit's last frame arrived, and the cases clicked so far."""

    url = f"/api/{DOMAIN}/status"
    name = f"api:{DOMAIN}:status"

    async def get(self, request: web.Request) -> web.Response:
        hass = _require_admin(request)
        now = dt_util.utcnow()
        store = photo_store(hass)
        photos = await hass.async_add_executor_job(store.files)
        return self.json(
            {
                "entries": [
                    {
                        "entry": entry.title,
                        "entry_id": entry.entry_id,
                        "seconds_since_last_frame": {
                            str(serial): age
                            for serial, age in entry.runtime_data.coordinator.seconds_since_last_frame(
                                now
                            ).items()
                        },
                        "markers": entry.runtime_data.coordinator.frame_log.markers(),
                        "not_downloaded": entry.runtime_data.coordinator.frame_log.not_downloaded(),
                    }
                    for entry in _loaded_entries(hass)
                ],
                "photos": len(photos),
            }
        )


class AsekoExportView(HomeAssistantView):
    """Frames, markers, diagnostics and photos as one zip."""

    url = f"/api/{DOMAIN}/export"
    name = f"api:{DOMAIN}:export"

    async def get(self, request: web.Request) -> web.Response:
        # Imported here: diagnostics imports the platforms, which import this
        # package's __init__, which sets this module up.
        from ..diagnostics import async_get_config_entry_diagnostics  # noqa: PLC0415

        hass = _require_admin(request)
        only_new = request.query.get("new") == "1"
        created = dt_util.now()
        loaded = _loaded_entries(hass)
        entries = []
        wanted_photos: set[str] = set()
        newest: dict[str, int] = {}
        for entry in loaded:
            log = entry.runtime_data.coordinator.frame_log
            markers = [m for m in log.markers() if not (only_new and m["downloaded"])]
            wanted_photos.update(m["photo"] for m in markers if m.get("photo"))
            newest[entry.entry_id] = max((m["n"] for m in log.markers()), default=0)
            snapshot = log.snapshot()
            entries.append(
                {
                    "title": entry.title,
                    "entry_id": entry.entry_id,
                    "records": await hass.async_add_executor_job(snapshot.records),
                    "cases": markers,
                    "diagnostics": await async_get_config_entry_diagnostics(
                        hass, entry
                    ),
                }
            )
        store = photo_store(hass)
        photos = await hass.async_add_executor_job(store.files)
        if only_new:
            photos = [p for p in photos if p.name in wanted_photos]
        body = await hass.async_add_executor_job(
            build_export_zip, entries, photos, created
        )
        for entry in loaded:
            entry.runtime_data.coordinator.mark_exported(newest[entry.entry_id])
        filename = f"aseko-local-export-{created.strftime('%Y%m%d-%H%M%S')}.zip"
        return web.Response(
            body=body,
            content_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
