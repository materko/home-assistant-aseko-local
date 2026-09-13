/*
 * Aseko mark card: mark test cases in the frame log, photograph the unit's
 * display, and download everything later from any device.
 *
 *   type: custom:aseko-mark-card
 *
 * Loaded on every dashboard by the Aseko Local integration.  Cases (markers)
 * and photos are kept in Home Assistant, so the list below is the same on a
 * phone and a PC, and shows which cases have not been downloaded yet.
 * Admin users only, like the diagnostics download.
 */

const STATUS_URL = "/api/aseko_local/status";
const PHOTO_URL = "/api/aseko_local/photo";
const EXPORT_URL = "/api/aseko_local/export";
const FORGET_URL = "/api/aseko_local/forget";

const esc = (text) =>
  String(text == null ? "" : text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class AsekoMarkCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._thumbs = {};
    this._listKey = "";
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 8;
  }

  static getStubConfig() {
    return {};
  }

  connectedCallback() {
    this._poll();
    this._timer = setInterval(() => this._poll(), 3000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  _render() {
    const title = this._config.title || "Aseko test cases";
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .row { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; align-items: center; }
        .age b { font-size: 1.3em; }
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
        h3 { margin: 18px 0 6px; font-size: 1.05em; }
        .cases { display: flex; flex-direction: column; gap: 6px; }
        .case { display: flex; gap: 10px; align-items: center; padding: 8px;
          border-radius: 8px; background: var(--secondary-background-color); }
        .case.new { border-left: 4px solid var(--warning-color, #ffa600); }
        .case img { width: 56px; height: 56px; object-fit: cover; border-radius: 6px; cursor: pointer; }
        .case .txt { flex: 1; min-width: 0; }
        .case .note { font-weight: 600; overflow-wrap: anywhere; }
        .case .meta { font-size: 0.85em; opacity: 0.8; }
        .empty { opacity: 0.7; }
      </style>
      <ha-card header="${esc(title)}">
        <div class="age" id="age">Last frame: \u2026</div>
        <div class="row">
          <input id="note" type="text" placeholder="What did you change? e.g. Heating control ON" maxlength="200">
        </div>
        <div class="row">
          <button id="photo">\u{1F4F7} Photo + mark</button>
          <button id="mark">\u{1F3C1} Mark</button>
          <label><input id="wait" type="checkbox" checked> wait for next frame</label>
        </div>
        <input id="file" type="file" accept="image/*" capture="environment" hidden>
        <div class="status" id="status">Mark each change; download the cases whenever you like.</div>
        <h3 id="heading">Cases</h3>
        <div class="cases" id="cases"><div class="empty">No cases yet.</div></div>
        <div class="row">
          <button id="export-new">\u2B07 Download new</button>
          <button id="export-all" class="secondary">\u2B07 Download all</button>
          <button id="forget" class="secondary">Clear list</button>
        </div>
      </ha-card>`;
    const $ = (id) => this.shadowRoot.getElementById(id);
    $("photo").addEventListener("click", () => $("file").click());
    $("file").addEventListener("change", (ev) => this._upload(ev.target));
    $("mark").addEventListener("click", () => this._mark());
    $("export-new").addEventListener("click", () => this._export(true));
    $("export-all").addEventListener("click", () => this._export(false));
    $("forget").addEventListener("click", () => this._forget());
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
    for (const id of ["photo", "mark", "export-new", "export-all", "forget"]) this._el(id).disabled = busy;
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
      this._renderCases(data.entries);
    } catch (err) {
      this._el("age").textContent = `Last frame: unavailable (${err.message})`;
    }
  }

  _renderCases(entries) {
    const cases = entries.flatMap((e) => e.markers || []).sort((a, b) => b.n - a.n);
    const fresh = entries.reduce((sum, e) => sum + (e.not_downloaded || 0), 0);
    this._el("heading").textContent = `Cases (${cases.length}, not downloaded: ${fresh})`;
    this._el("export-new").textContent = `\u2B07 Download new (${fresh})`;
    const key = JSON.stringify(cases.map((c) => [c.n, c.downloaded, c.frames, c.photo]));
    if (key === this._listKey) return;
    this._listKey = key;
    const list = this._el("cases");
    if (!cases.length) {
      list.innerHTML = '<div class="empty">No cases yet.</div>';
      return;
    }
    list.innerHTML = cases
      .map((c) => {
        const when = new Date(c.t).toLocaleString();
        const flags = [
          c.downloaded ? "downloaded" : "NOT downloaded",
          c.frames ? "frames kept" : "frames aged out",
        ].join(" \u00B7 ");
        const img = c.photo ? `<img data-photo="${esc(c.photo)}" alt="photo">` : "";
        return `<div class="case ${c.downloaded ? "" : "new"}">${img}
          <div class="txt"><div class="note">#${c.n} ${esc(c.note || "(no note)")}</div>
          <div class="meta">${esc(when)} \u00B7 ${flags}</div></div></div>`;
      })
      .join("");
    for (const img of list.querySelectorAll("img[data-photo]")) this._loadThumb(img);
  }

  async _loadThumb(img) {
    const name = img.dataset.photo;
    if (!this._thumbs[name]) {
      this._thumbs[name] = this._hass
        .fetchWithAuth(`${PHOTO_URL}/${encodeURIComponent(name)}`)
        .then((r) => (r.ok ? r.blob() : null))
        .then((blob) => (blob ? URL.createObjectURL(blob) : null))
        .catch(() => null);
    }
    const url = await this._thumbs[name];
    if (url) {
      img.src = url;
      img.onclick = () => window.open(url, "_blank");
    }
  }

  _note() {
    return this._el("note").value.trim();
  }

  _describe(markers, extra) {
    return markers
      .map((m) => `Case #${m.marker} saved at ${new Date(m.time).toLocaleTimeString()}${extra || ""}`)
      .join("\n");
  }

  async _upload(input) {
    const file = input.files && input.files[0];
    input.value = "";
    if (!file) return;
    this._busy(true);
    this._setStatus("Uploading photo\u2026 the case is not saved yet.", "waiting");
    try {
      const form = new FormData();
      form.append("note", this._note());
      form.append("photo", file, file.name || "photo.jpg");
      const response = await this._hass.fetchWithAuth(PHOTO_URL, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
      this._setStatus(this._describe(data.markers, " with photo"), "done");
      this._el("note").value = "";
      this._poll();
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
      wait ? "Waiting for the next frame\u2026 the case is not saved yet, leave the unit as it is." : "Saving case\u2026",
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
          : `${this._describe(markers)}${wait ? " \u2014 frame received, go on with the next change." : ""}`,
        late ? "error" : "done",
      );
      this._el("note").value = "";
      this._poll();
    } catch (err) {
      this._setStatus(`Case not saved: ${err.message}`, "error");
    } finally {
      this._busy(false);
    }
  }

  async _export(onlyNew) {
    this._busy(true);
    this._setStatus("Building the zip\u2026", "waiting");
    try {
      const response = await this._hass.fetchWithAuth(`${EXPORT_URL}${onlyNew ? "?new=1" : ""}`);
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
      this._poll();
    } catch (err) {
      this._setStatus(`Download failed: ${err.message}`, "error");
    } finally {
      this._busy(false);
    }
  }

  async _forget() {
    if (!window.confirm("Clear the list of cases? Frames and photos stay in Home Assistant.")) return;
    this._busy(true);
    try {
      const response = await this._hass.fetchWithAuth(FORGET_URL, { method: "POST" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      this._setStatus("List cleared.", "done");
      this._poll();
    } catch (err) {
      this._setStatus(`Not cleared: ${err.message}`, "error");
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
    name: "Aseko test cases",
    description: "Mark test cases in the Aseko frame log, photograph the unit's display and download them from any device.",
  });
}
