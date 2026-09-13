/*
 * Aseko mark card: mark the frame log, photograph the unit's display, export.
 *
 *   type: custom:aseko-mark-card
 *
 * Loaded on every dashboard by the Aseko Local integration.  The camera
 * button opens the phone camera; the photo goes to Home Assistant and the
 * marker is written the moment it arrives, so photos and frames line up
 * without EXIF data, file names or clocks.  Admin users only, like the
 * diagnostics download.
 */

const STATUS_URL = "/api/aseko_local/status";
const PHOTO_URL = "/api/aseko_local/photo";
const EXPORT_URL = "/api/aseko_local/export";

class AsekoMarkCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {};
  }

  connectedCallback() {
    this._poll();
    this._timer = setInterval(() => this._poll(), 2000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  _render() {
    const title = this._config.title || "Aseko mark";
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .row { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        .age { font-size: 1.1em; }
        .age b { font-size: 1.4em; }
        input[type=text] { flex: 1; min-width: 0; padding: 8px; font-size: 1em;
          border: 1px solid var(--divider-color); border-radius: 6px;
          background: var(--card-background-color); color: var(--primary-text-color); }
        button { padding: 10px 14px; font-size: 1em; border: 0; border-radius: 8px;
          background: var(--primary-color); color: var(--text-primary-color, #fff); cursor: pointer; }
        button.secondary { background: var(--secondary-background-color); color: var(--primary-text-color); }
        button:disabled { opacity: 0.5; }
        .status { margin-top: 12px; padding: 10px; border-radius: 8px;
          background: var(--secondary-background-color); white-space: pre-line; }
        .waiting { background: var(--warning-color, #ffa600); color: #000; }
        .done { background: var(--success-color, #43a047); color: #fff; }
        .error { background: var(--error-color, #db4437); color: #fff; }
        label { display: flex; align-items: center; gap: 6px; }
      </style>
      <ha-card header="${title}">
        <div class="age" id="age">Last frame: \u2026</div>
        <div class="row">
          <input id="note" type="text" placeholder="Note, e.g. Heating control ON" maxlength="200">
        </div>
        <div class="row">
          <button id="photo">\u{1F4F7} Photo + mark</button>
          <button id="mark">\u{1F3C1} Mark</button>
          <label><input id="wait" type="checkbox"> wait for next frame</label>
        </div>
        <input id="file" type="file" accept="image/*" capture="environment" hidden>
        <div class="status" id="status">No marker written yet.</div>
        <div class="row">
          <button id="export" class="secondary">\u2B07 Export zip (frames + photos)</button>
        </div>
      </ha-card>`;
    const $ = (id) => this.shadowRoot.getElementById(id);
    $("photo").addEventListener("click", () => $("file").click());
    $("file").addEventListener("change", (ev) => this._upload(ev.target));
    $("mark").addEventListener("click", () => this._mark());
    $("export").addEventListener("click", () => this._export());
  }

  _el(id) {
    return this.shadowRoot.getElementById(id);
  }

  _setStatus(text, kind) {
    const el = this._el("status");
    el.textContent = text;
    el.className = `status ${kind || ""}`;
  }

  _busy(busy) {
    for (const id of ["photo", "mark", "export"]) this._el(id).disabled = busy;
  }

  async _poll() {
    if (!this._hass || !this.shadowRoot) return;
    try {
      const response = await this._hass.fetchWithAuth(STATUS_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const ages = data.entries.flatMap((e) => Object.values(e.seconds_since_last_frame));
      this._el("age").innerHTML = ages.length
        ? `Last frame: <b>${Math.round(Math.min(...ages))} s</b> ago`
        : "Last frame: none received yet";
    } catch (err) {
      this._el("age").textContent = `Last frame: unavailable (${err.message})`;
    }
  }

  _note() {
    return this._el("note").value.trim();
  }

  _describe(markers, extra) {
    return markers
      .map((m) => `Marker ${m.marker} written at ${new Date(m.time).toLocaleTimeString()}${extra || ""}`)
      .join("\n");
  }

  async _upload(input) {
    const file = input.files && input.files[0];
    input.value = "";
    if (!file) return;
    this._busy(true);
    this._setStatus("Uploading photo\u2026 the marker is not written yet.", "waiting");
    try {
      const form = new FormData();
      form.append("note", this._note());
      form.append("photo", file, file.name || "photo.jpg");
      const response = await this._hass.fetchWithAuth(PHOTO_URL, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
      this._setStatus(`${this._describe(data.markers, " with photo")}\n${data.photo}`, "done");
    } catch (err) {
      this._setStatus(`Photo not stored: ${err.message}`, "error");
    } finally {
      this._busy(false);
    }
  }

  async _mark() {
    const wait = this._el("wait").checked;
    this._busy(true);
    this._setStatus(
      wait ? "Waiting for the next frame\u2026 the marker is not written yet, leave the unit as it is." : "Writing marker\u2026",
      "waiting",
    );
    try {
      const serviceData = { wait_for_next_frame: wait };
      if (this._note()) serviceData.note = this._note();
      const result = await this._hass.callWS({
        type: "call_service",
        domain: "aseko_local",
        service: "mark_dump",
        service_data: serviceData,
        return_response: true,
      });
      const markers = result.response.markers;
      const late = wait && markers.some((m) => !m.waited_for_frame);
      this._setStatus(
        late
          ? `No frame within 60 s.\n${this._describe(markers)} without one.`
          : `${this._describe(markers)}${wait ? " \u2014 frame received, you can change the unit again." : ""}`,
        late ? "error" : "done",
      );
    } catch (err) {
      this._setStatus(`Marker not written: ${err.message}`, "error");
    } finally {
      this._busy(false);
    }
  }

  async _export() {
    this._busy(true);
    this._setStatus("Building the zip\u2026", "waiting");
    try {
      const response = await this._hass.fetchWithAuth(EXPORT_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = /filename="([^"]+)"/.exec(disposition);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = match ? match[1] : "aseko-local-export.zip";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 60000);
      this._setStatus(`Zip downloaded (${Math.round(blob.size / 1024)} kB).`, "done");
    } catch (err) {
      this._setStatus(`Export failed: ${err.message}`, "error");
    } finally {
      this._busy(false);
    }
  }
}

if (!customElements.get("aseko-mark-card")) {
  customElements.define("aseko-mark-card", AsekoMarkCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "aseko-mark-card",
    name: "Aseko mark",
    description: "Mark the Aseko frame log, photograph the unit's display and export frames with photos.",
  });
}
