# custom_components/aseko_local/coordinator.py

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from types import CoroutineType
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .models import AsekoData, AsekoDevice
from .recording.frame_log import KIND_PARTIAL, KIND_V7, KIND_V8, FrameLog
from .trackers.backwash import BackwashTracker
from .trackers.consumption import AsekoConsumptionTracker

_LOGGER = logging.getLogger(__name__)

FRAME_LOG_STORAGE_VERSION = 1
FRAME_LOG_STORAGE_KEY_PREFIX = "aseko_local_frame_log_"
# How long after a request the frame log is written, and how often frames may
# request it: a crash loses at most a few minutes of frames.
FRAME_LOG_SAVE_DELAY = 60
FRAME_LOG_SAVE_INTERVAL = timedelta(minutes=10)


class AsekoLocalDataUpdateCoordinator(DataUpdateCoordinator[AsekoData]):
    """Aseko Local coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        cb_new_device: Callable[[AsekoDevice], CoroutineType[Any, Any, None]]
        | None = None,
    ) -> None:
        """Initialize coordinator."""
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.cb_new_device = cb_new_device
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
        )
        # One tracker per device serial number
        self._trackers: dict[int, AsekoConsumptionTracker] = {}
        # One backwash tracker per device serial number
        self._backwash_trackers: dict[int, BackwashTracker] = {}
        # Last raw frame per device serial number (for diagnostics)
        self._last_raw_frames: dict[int, bytes] = {}
        # Last partial (incomplete) raw frame per serial number
        self._last_partial_frames: dict[int, bytes] = {}
        # Last raw v8 text frame per device serial number (for diagnostics)
        self._last_v8_frames: dict[int, bytes] = {}
        # Last decoding of every unit whose type nobody has mapped, by serial
        # number -- kept for diagnostics only, never handed to the platforms
        self._unrecognised_devices: dict[int, AsekoDevice] = {}
        # Every frame received plus mark_dump markers, capped in compressed
        # bytes, for the diagnostics download; persisted across restarts
        self.frame_log = FrameLog()
        self._frame_log_store: Store[dict[str, Any]] | None = None
        self._frame_log_save_requested: datetime | None = None
        # When each unit's last frame arrived, and mark_dump calls waiting for
        # the next one
        self._last_frame_at: dict[int, datetime] = {}
        self._frame_waiters: list[asyncio.Future[None]] = []
        # Why the server found a unit's frames implausible, by serial number
        # and reason -- for diagnostics
        self._frame_warnings: dict[int, dict[str, dict[str, Any]]] = {}
        # Unsubscribe handle for the periodic stale-check
        self._stale_check_unsub: Callable[[], None] | None = None
        # Per-platform listeners called whenever a brand-new device is discovered
        self._new_device_listeners: list[Callable[[AsekoDevice], None]] = []
        # Per-platform listeners called when a known device shows features it
        # has not shown before, with the names of those features
        self._new_features_listeners: list[
            Callable[[AsekoDevice, frozenset[str]], None]
        ] = []

    def devices_update_callback(self, device: AsekoDevice) -> None:
        """Receive callback with device update."""

        # A frame from a unit type nobody has mapped.  It gets no entities --
        # nothing about it is verified -- but it is kept aside so the
        # diagnostics download can show its raw frame and the generic
        # decoding, which is exactly what is needed to map it.
        if getattr(device, "device_type", None) is None:
            serial = getattr(device, "serial_number", None)
            if serial is not None and serial not in self._unrecognised_devices:
                _LOGGER.warning(
                    "❌ Received device with unknown type, not stored! serial=%s. "
                    "Please share a diagnostics download at "
                    "https://github.com/hopkins-tk/home-assistant-aseko-local/issues",
                    serial,
                )
            if serial is not None:
                self._unrecognised_devices[serial] = device
            return

        _LOGGER.debug(
            "📡 devices_update_callback CALLED with device=%s (serial=%s)",
            device,
            getattr(device, "serial_number", None),
        )

        new_data: AsekoData = AsekoData() if self.data is None else self.data

        existing_serials = [d.serial_number for d in (new_data.get_all() or [])]
        _LOGGER.debug("🔎 Before update: known serials=%s", existing_serials)

        is_new_device = False
        grown: frozenset[str] = frozenset()

        if device.serial_number is not None:
            existing = new_data.get(device.serial_number)
            is_new_device = existing is None
            _LOGGER.debug(
                "➡️ Device %s is_new_device=%s", device.serial_number, is_new_device
            )
            grown = self._merge_features(device, existing)

            # Fill the observed-backwash fields *before* handing the device to
            # AsekoData.set(): for an already-known device, set() copies the
            # attributes off this object onto the stored one, and anything
            # written afterwards would never reach the entities.
            self._update_backwash(device)

            new_data.set(device.serial_number, device)

            # Stamp server-side receive time (independent of device clock)
            stored = new_data.get(device.serial_number)
            if stored is not None:
                stored.last_seen = dt_util.now()

            # Update consumption tracker for this device
            if device.serial_number not in self._trackers:
                self._trackers[device.serial_number] = AsekoConsumptionTracker()
            self._trackers[device.serial_number].update(device, dt_util.now())

            _LOGGER.debug(
                "✅ Stored device %s → known serials now: %s",
                device.serial_number,
                list(new_data.devices.keys()),
            )
        else:
            _LOGGER.error("❌ Received device without serial_number, not stored!")
            return  # abort, nothing to propagate

        devices = new_data.get_all() or []
        _LOGGER.debug("📊 Currently %s devices in new_data", len(devices))

        _LOGGER.debug(
            "⚠️ Calling async_set_updated_data() with %s devices", len(devices)
        )
        self.async_set_updated_data(new_data)

        if is_new_device:
            _LOGGER.debug("🆕 NEW DEVICE DISCOVERED: %s", device.serial_number)
            if self.cb_new_device is not None:
                self.hass.loop.create_task(self.cb_new_device(device))
            for listener in list(self._new_device_listeners):
                try:
                    listener(device)
                except Exception:
                    _LOGGER.exception(
                        "❌ New-device listener %r failed for device serial=%s",
                        listener,
                        device.serial_number,
                    )
        elif grown:
            # The unit has shown quantities it had not shown before -- the
            # shared pump port got configured, a setting was made, byte[37]
            # became readable.  Hand the platforms the stored device (the
            # object the existing entities read) so they can add the missing
            # entities without a reload.
            stored = new_data.get(device.serial_number)
            _LOGGER.debug(
                "🧩 Device %s shows new features: %s",
                device.serial_number,
                sorted(grown),
            )
            for listener in list(self._new_features_listeners):
                try:
                    listener(stored, grown)
                except Exception:
                    _LOGGER.exception(
                        "❌ New-features listener %r failed for device serial=%s",
                        listener,
                        device.serial_number,
                    )

    @staticmethod
    def _merge_features(
        device: AsekoDevice, existing: AsekoDevice | None
    ) -> frozenset[str]:
        """Make presence sticky and return what this frame added.

        Once a unit has shown a quantity it has it, whatever a later frame
        could or could not read (a shared port reconfigured, a probe briefly
        unreadable), so the stored device's feature set only ever grows.  The
        returned set is what the entity platforms have not been told about
        yet; empty for a device seen for the first time, whose whole feature
        set goes out through the new-device listeners instead.
        """
        if existing is None:
            return frozenset()
        grown = device.features - existing.features
        device.features = device.features | existing.features
        return grown

    def _update_backwash(self, device: AsekoDevice) -> None:
        """Feed the frame to the device's BackwashTracker and publish its state.

        The device transmits only the backwash *configuration* and the live
        relay bit, never its history, so every observed-backwash field on
        ``AsekoDevice`` comes from the tracker.  They stay None until a real
        cycle has been seen, which is what makes the sensors read "unknown"
        rather than showing a schedule-derived guess.

        Lazy-load persisted state on the first frame after a restart so the
        saved timestamps survive reloads.  Doing it here (rather than in
        ``async_setup_backwash_trackers``) avoids a race where the tracker is
        created on the first frame *before* the setup hook has had a chance to
        load its persisted state.
        """
        serial = device.serial_number
        if serial is None:
            return

        if serial not in self._backwash_trackers:
            new_tracker = BackwashTracker(self.hass, serial)
            self._backwash_trackers[serial] = new_tracker
            self.hass.async_create_task(new_tracker.async_load())

        tracker = self._backwash_trackers[serial]
        now = dt_util.now()
        tracker.update(device, now)
        self._publish_backwash(device, tracker, now)

    @staticmethod
    def _publish_backwash(
        device: AsekoDevice, tracker: BackwashTracker, now: datetime
    ) -> None:
        """Copy the tracker's state onto the device object the entities read."""
        device.last_backwash = tracker.last_backwash
        device.last_scheduled_backwash = tracker.last_scheduled_backwash
        device.last_scheduled_backwash_source = tracker.last_scheduled_source
        device.last_manual_backwash = tracker.last_manual_backwash
        device.last_backwash_trigger = tracker.last_trigger
        device.next_scheduled_backwash = tracker.next_scheduled_backwash(device, now)

    def set_last_scheduled_backwash(
        self, moment: datetime, serial_number: int | None = None
    ) -> bool:
        """Seed the last scheduled backwash for one device, or for all of them."""
        return self._apply_to_backwash_trackers(
            lambda tracker: tracker.set_last_scheduled_backwash(moment),
            serial_number,
        )

    def clear_last_scheduled_backwash(self, serial_number: int | None = None) -> bool:
        """Forget the last scheduled backwash for one device, or for all of them."""
        return self._apply_to_backwash_trackers(
            lambda tracker: tracker.clear_last_scheduled_backwash(),
            serial_number,
        )

    def _apply_to_backwash_trackers(
        self,
        action: Callable[[BackwashTracker], None],
        serial_number: int | None,
    ) -> bool:
        """Run ``action`` on the matching trackers and republish their state.

        Backs the ``aseko_local.*_last_scheduled_backwash`` services.  Returns
        True if at least one tracker matched, so the service can tell the user
        when a serial number matched nothing.

        The stored device objects are updated in place and listeners notified,
        so the entities reflect the change straight away instead of waiting for
        the next frame.
        """
        if serial_number is not None:
            trackers = {
                serial: tracker
                for serial, tracker in self._backwash_trackers.items()
                if serial == serial_number
            }
        else:
            trackers = dict(self._backwash_trackers)

        if not trackers:
            return False

        for serial, tracker in trackers.items():
            action(tracker)
            device = self.get_device(serial)
            if device is not None:
                self._publish_backwash(device, tracker, dt_util.now())

        self.async_update_listeners()
        return True

    def async_add_new_device_listener(
        self, listener: Callable[[AsekoDevice], None]
    ) -> Callable[[], None]:
        """Register a callback invoked whenever a brand-new device is discovered.

        Returns an unsubscribe callable that removes the listener.
        Platforms call this in async_setup_entry and pass the result to
        config_entry.async_on_unload() so the listener is removed on unload.
        """
        self._new_device_listeners.append(listener)

        def _unsub() -> None:
            self._new_device_listeners.remove(listener)

        return _unsub

    def async_add_new_features_listener(
        self, listener: Callable[[AsekoDevice, frozenset[str]], None]
    ) -> Callable[[], None]:
        """Register a callback for a known device that shows new features.

        Called with the stored device and the names of the AsekoDevice fields
        that were not in its feature set before this frame.  Platforms build
        just the entities for those fields, so a quantity that only becomes
        present after the device was first seen still gets its entity.
        Returns an unsubscribe callable, like ``async_add_new_device_listener``.
        """
        self._new_features_listeners.append(listener)

        def _unsub() -> None:
            self._new_features_listeners.remove(listener)

        return _unsub

    def store_raw_frame(self, raw_frame: bytes) -> None:
        """Cache the last raw frame, keyed by serial number (bytes 0-3).

        Frames shorter than MESSAGE_SIZE are stored as partial frames so users
        with unknown device variants can share the raw data via the Diagnostics
        download without needing to enable debug logging.
        """
        if len(raw_frame) < 4:
            return
        serial = int.from_bytes(raw_frame[0:4], "big")
        from .const import MESSAGE_SIZE  # noqa: PLC0415

        if len(raw_frame) < MESSAGE_SIZE:
            self._last_partial_frames[serial] = bytes(raw_frame)
            self._log_frame(KIND_PARTIAL, raw_frame, serial)
        else:
            self._last_raw_frames[serial] = bytes(raw_frame)
            self._log_frame(KIND_V7, raw_frame, serial)

    def store_frame_warning(self, serial_number: int, reason: str) -> None:
        """Count one implausible frame from a unit, by reason, for diagnostics."""
        now = dt_util.utcnow().isoformat()
        entry = self._frame_warnings.setdefault(serial_number, {}).setdefault(
            reason, {"count": 0, "first_seen": now}
        )
        entry["count"] += 1
        entry["last_seen"] = now

    def get_frame_warnings(self, serial_number: int) -> dict[str, dict[str, Any]]:
        """Return the implausible-frame reasons recorded for a serial number."""
        return self._frame_warnings.get(serial_number, {})

    def get_raw_frame(self, serial_number: int) -> bytes | None:
        """Return the last full raw frame for a given device serial number."""
        return self._last_raw_frames.get(serial_number)

    def get_partial_frame(self, serial_number: int) -> bytes | None:
        """Return the last partial (incomplete) raw frame, if any."""
        return self._last_partial_frames.get(serial_number)

    def store_v8_frame(self, raw_frame: bytes) -> None:
        """Cache the last v8 text frame, keyed by the serial number in the frame text."""
        try:
            text = raw_frame.decode("ascii", errors="replace").strip()
            # Frame starts with "{v1 <serial> ..."
            serial: int | None = int(text.lstrip("{").split()[1])
            self._last_v8_frames[serial] = bytes(raw_frame)
        except (ValueError, IndexError):
            serial = None
        self._log_frame(KIND_V8, raw_frame, serial)

    # -- frame log -----------------------------------------------------------

    async def async_load_frame_log(self) -> None:
        """Restore the frame log saved before the last restart."""
        self._frame_log_store = Store(
            self.hass,
            FRAME_LOG_STORAGE_VERSION,
            f"{FRAME_LOG_STORAGE_KEY_PREFIX}{self.config_entry.entry_id}",
        )
        data = await self._frame_log_store.async_load()
        if data:
            self.frame_log.load_store(data)

    async def async_save_frame_log(self) -> None:
        """Write the frame log now (on unload)."""
        if self._frame_log_store is not None:
            await self._frame_log_store.async_save(self.frame_log.to_store())

    def _log_frame(self, kind: str, raw_frame: bytes, serial: int | None) -> None:
        received = dt_util.utcnow()
        self.frame_log.append_frame(received, kind, raw_frame)
        if serial is not None:
            self._last_frame_at[serial] = received
        for waiter in self._frame_waiters:
            if not waiter.done():
                waiter.set_result(None)
        self._frame_waiters.clear()
        self._request_frame_log_save()

    async def async_wait_for_frame(self, timeout: float) -> bool:
        """Wait for the next frame from any unit; False if none came in time."""
        waiter: asyncio.Future[None] = self.hass.loop.create_future()
        self._frame_waiters.append(waiter)
        try:
            await asyncio.wait_for(waiter, timeout)
        except TimeoutError:
            return False
        finally:
            if waiter in self._frame_waiters:
                self._frame_waiters.remove(waiter)
        return True

    def seconds_since_last_frame(self, now: datetime) -> dict[int, float]:
        """How long ago each unit's last frame arrived, by serial number."""
        return {
            serial: round((now - received).total_seconds(), 1)
            for serial, received in self._last_frame_at.items()
        }

    def _request_frame_log_save(self, delay: float = FRAME_LOG_SAVE_DELAY) -> None:
        """Save the log soon, but at most once per interval while frames flow.

        Store.async_delay_save restarts its timer on every call, so calling it
        for every frame would postpone the write forever.  The store also
        writes the latest state when Home Assistant stops.
        """
        if self._frame_log_store is None:
            return
        now = dt_util.utcnow()
        if (
            delay >= FRAME_LOG_SAVE_DELAY
            and self._frame_log_save_requested is not None
            and now - self._frame_log_save_requested < FRAME_LOG_SAVE_INTERVAL
        ):
            return
        self._frame_log_save_requested = now
        self._frame_log_store.async_delay_save(self.frame_log.to_store, delay)

    def mark_dump(
        self, note: str | None = None, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Write a numbered marker into the frame log and describe it.

        The marker records how many seconds ago each unit's last frame
        arrived, so a reader can tell whether the change it marks could
        already be in that frame.
        """
        received = dt_util.utcnow()
        since = self.seconds_since_last_frame(received)
        number = self.frame_log.append_marker(
            received,
            note,
            {str(serial): age for serial, age in since.items()},
            extra,
        )
        _LOGGER.info(
            "Aseko frame log marker %s at %s %s (last frame %s s ago)",
            number,
            received,
            note or "",
            since,
        )
        self._request_frame_log_save(delay=5)
        return {
            "marker": number,
            "time": received,
            "seconds_since_last_frame": since,
        }

    def mark_exported(self, through: int) -> None:
        """Record that markers up to ``through`` were downloaded, and save."""
        self.frame_log.mark_exported(through)
        self._request_frame_log_save(delay=5)

    def forget_markers(self) -> None:
        """Clear the list of cases shown on the mark card, and save."""
        self.frame_log.forget_markers()
        self._request_frame_log_save(delay=5)

    def get_v8_frame(self, serial_number: int) -> bytes | None:
        """Return the last raw v8 text frame for a given device serial number."""
        return self._last_v8_frames.get(serial_number)

    def get_unrecognised_devices(self) -> list[AsekoDevice]:
        """Return the units whose type nobody has mapped, as last decoded."""
        return list(self._unrecognised_devices.values())

    def get_tracker(self, serial_number: int) -> AsekoConsumptionTracker | None:
        """Return the consumption tracker for a given device serial number."""
        return self._trackers.get(serial_number)

    def reset_consumption(self, pump_key: str, counter: str) -> None:
        """Reset consumption counters for all tracked devices and notify listeners."""
        for tracker in self._trackers.values():
            tracker.reset(pump_key=pump_key, counter=counter)
        self.async_update_listeners()

    def get_device(self, serial_number: int) -> AsekoDevice | None:
        _LOGGER.debug("get_device(%s) called", serial_number)
        return self.data.get(serial_number) if self.data is not None else None

    def get_devices(self) -> list[AsekoDevice]:
        devices = self.data.get_all() or [] if self.data is not None else []
        _LOGGER.debug(
            "get_devices() → %s devices: %s",
            len(devices),
            [d.serial_number for d in devices],
        )
        return devices

    def get_backwash_tracker(self, serial_number: int) -> BackwashTracker | None:
        """Return the backwash tracker for a given device serial number."""
        return self._backwash_trackers.get(serial_number)

    async def async_setup_backwash_trackers(self) -> None:
        """Pre-load persisted backwash timestamps from storage.

        This is a best-effort warm-up: trackers are also created
        lazily on the first received frame in
        :meth:`devices_update_callback`, which is the only path that
        matters because the integration does not know device serials
        before any frame arrives.  This method just gives already-known
        devices a head start on loading from disk.
        """
        if self.data is None:
            return
        for device in self.data.get_all() or []:
            serial = device.serial_number
            if serial is None or serial in self._backwash_trackers:
                continue
            tracker = BackwashTracker(self.hass, serial)
            self._backwash_trackers[serial] = tracker
            await tracker.async_load()

    def async_start_stale_check(self) -> None:
        """Start a periodic task that pushes updates so entities detect offline state."""
        self._stale_check_unsub = async_track_time_interval(
            self.hass,
            self._async_check_stale,
            timedelta(seconds=30),
        )

    @callback
    def _async_check_stale(self, _now: object) -> None:
        """Re-push current data so entities re-evaluate device.online()."""
        if self.data is not None:
            self.async_set_updated_data(self.data)

    def async_stop_stale_check(self) -> None:
        """Stop the periodic stale check."""
        if self._stale_check_unsub is not None:
            self._stale_check_unsub()
            self._stale_check_unsub = None
