/*
 * Aseko mark card: mark test cases in the frame log, photograph the unit's
 * display, and download everything later from any device.
 *
 *   type: custom:aseko-mark-card
 *   language: sk   # optional; defaults to the Home Assistant user language
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

const STRINGS = {
  "en": {
    "title": "Aseko test cases",
    "last_frame": "Last frame: {v}",
    "last_frame_ago": "Last frame: <b>{s} s</b> ago",
    "last_frame_none": "Last frame: none received yet",
    "last_frame_error": "Last frame: unavailable ({e})",
    "placeholder": "What did you change? e.g. Heating control ON",
    "photo_mark": "Photo + mark",
    "mark": "Mark",
    "wait": "wait for next frame",
    "intro": "Mark each change; download the cases whenever you like.",
    "cases": "Cases",
    "cases_count": "Cases ({n}, not downloaded: {f})",
    "no_cases": "No cases yet.",
    "download_new": "Download new",
    "download_all": "Download all",
    "clear": "Clear list",
    "downloaded": "downloaded",
    "not_downloaded": "NOT downloaded",
    "frames_kept": "frames kept",
    "frames_gone": "frames aged out",
    "no_note": "(no note)",
    "photo": "photo",
    "case_saved": "Case #{n} saved at {time}",
    "with_photo": " with photo",
    "uploading": "Uploading photo\u2026 the case is not saved yet.",
    "photo_failed": "Photo not stored: {e}",
    "waiting": "Waiting for the next frame\u2026 the case is not saved yet, leave the unit as it is.",
    "saving": "Saving case\u2026",
    "no_frame": "No frame within 60 s.\n{cases} without one.",
    "frame_received": " \u2014 frame received, go on with the next change.",
    "mark_failed": "Case not saved: {e}",
    "zipping": "Building the zip\u2026",
    "zipped": "Zip downloaded ({kb} kB).",
    "download_failed": "Download failed: {e}",
    "clear_confirm": "Clear the list of cases? Frames and photos stay in Home Assistant.",
    "cleared": "List cleared.",
    "clear_failed": "Not cleared: {e}"
  },
  "sk": {
    "title": "Aseko \u2013 z\u00e1znam pokusov",
    "last_frame": "Posledn\u00fd r\u00e1mec: {v}",
    "last_frame_ago": "Posledn\u00fd r\u00e1mec: pred <b>{s} s</b>",
    "last_frame_none": "Posledn\u00fd r\u00e1mec: zatia\u013e \u017eiadny",
    "last_frame_error": "Posledn\u00fd r\u00e1mec: nedostupn\u00e9 ({e})",
    "placeholder": "\u010co si zmenil? napr. Ohrev ZAP",
    "photo_mark": "Fotka + z\u00e1znam",
    "mark": "Z\u00e1znam",
    "wait": "po\u010dka\u0165 na \u010fal\u0161\u00ed r\u00e1mec",
    "intro": "Zaznamenaj ka\u017ed\u00fa zmenu; pokusy si stiahni kedyko\u013evek.",
    "cases": "Pokusy",
    "cases_count": "Pokusy ({n}, nestiahnut\u00e9: {f})",
    "no_cases": "Zatia\u013e \u017eiadne pokusy.",
    "download_new": "Stiahnu\u0165 nov\u00e9",
    "download_all": "Stiahnu\u0165 v\u0161etko",
    "clear": "Vymaza\u0165 zoznam",
    "downloaded": "stiahnut\u00e9",
    "not_downloaded": "NESTIAHNUT\u00c9",
    "frames_kept": "r\u00e1mce ulo\u017een\u00e9",
    "frames_gone": "r\u00e1mce u\u017e vypadli",
    "no_note": "(bez pozn\u00e1mky)",
    "photo": "fotka",
    "case_saved": "Pokus #{n} ulo\u017een\u00fd o {time}",
    "with_photo": " s fotkou",
    "uploading": "Nahr\u00e1vam fotku\u2026 pokus e\u0161te nie je ulo\u017een\u00fd.",
    "photo_failed": "Fotka neulo\u017een\u00e1: {e}",
    "waiting": "\u010cak\u00e1m na \u010fal\u0161\u00ed r\u00e1mec\u2026 pokus e\u0161te nie je ulo\u017een\u00fd, na jednotke ni\u010d neme\u0148.",
    "saving": "Uklad\u00e1m pokus\u2026",
    "no_frame": "\u017diadny r\u00e1mec do 60 s.\n{cases} bez neho.",
    "frame_received": " \u2014 r\u00e1mec pri\u0161iel, m\u00f4\u017ee\u0161 robi\u0165 \u010fal\u0161iu zmenu.",
    "mark_failed": "Pokus neulo\u017een\u00fd: {e}",
    "zipping": "Vytv\u00e1ram zip\u2026",
    "zipped": "Zip stiahnut\u00fd ({kb} kB).",
    "download_failed": "S\u0165ahovanie zlyhalo: {e}",
    "clear_confirm": "Vymaza\u0165 zoznam pokusov? R\u00e1mce a fotky ostan\u00fa v Home Assistante.",
    "cleared": "Zoznam vymazan\u00fd.",
    "clear_failed": "Nevymazan\u00e9: {e}"
  },
  "cs": {
    "title": "Aseko \u2013 z\u00e1znam pokus\u016f",
    "last_frame": "Posledn\u00ed r\u00e1mec: {v}",
    "last_frame_ago": "Posledn\u00ed r\u00e1mec: p\u0159ed <b>{s} s</b>",
    "last_frame_none": "Posledn\u00ed r\u00e1mec: zat\u00edm \u017e\u00e1dn\u00fd",
    "last_frame_error": "Posledn\u00ed r\u00e1mec: nedostupn\u00e9 ({e})",
    "placeholder": "Co jste zm\u011bnili? nap\u0159. Oh\u0159ev ZAP",
    "photo_mark": "Fotka + z\u00e1znam",
    "mark": "Z\u00e1znam",
    "wait": "po\u010dkat na dal\u0161\u00ed r\u00e1mec",
    "intro": "Zaznamenejte ka\u017edou zm\u011bnu; pokusy si st\u00e1hn\u011bte kdykoli.",
    "cases": "Pokusy",
    "cases_count": "Pokusy ({n}, nesta\u017eeno: {f})",
    "no_cases": "Zat\u00edm \u017e\u00e1dn\u00e9 pokusy.",
    "download_new": "St\u00e1hnout nov\u00e9",
    "download_all": "St\u00e1hnout v\u0161e",
    "clear": "Vymazat seznam",
    "downloaded": "sta\u017eeno",
    "not_downloaded": "NESTA\u017dENO",
    "frames_kept": "r\u00e1mce ulo\u017eeny",
    "frames_gone": "r\u00e1mce u\u017e vypadly",
    "no_note": "(bez pozn\u00e1mky)",
    "photo": "fotka",
    "case_saved": "Pokus #{n} ulo\u017een v {time}",
    "with_photo": " s fotkou",
    "uploading": "Nahr\u00e1v\u00e1m fotku\u2026 pokus je\u0161t\u011b nen\u00ed ulo\u017een.",
    "photo_failed": "Fotka neulo\u017eena: {e}",
    "waiting": "\u010cek\u00e1m na dal\u0161\u00ed r\u00e1mec\u2026 pokus je\u0161t\u011b nen\u00ed ulo\u017een, na jednotce nic nem\u011b\u0148te.",
    "saving": "Ukl\u00e1d\u00e1m pokus\u2026",
    "no_frame": "\u017d\u00e1dn\u00fd r\u00e1mec do 60 s.\n{cases} bez n\u011bj.",
    "frame_received": " \u2014 r\u00e1mec p\u0159i\u0161el, pokra\u010dujte dal\u0161\u00ed zm\u011bnou.",
    "mark_failed": "Pokus neulo\u017een: {e}",
    "zipping": "Vytv\u00e1\u0159\u00edm zip\u2026",
    "zipped": "Zip sta\u017een ({kb} kB).",
    "download_failed": "Stahov\u00e1n\u00ed selhalo: {e}",
    "clear_confirm": "Vymazat seznam pokus\u016f? R\u00e1mce a fotky z\u016fstanou v Home Assistantu.",
    "cleared": "Seznam vymaz\u00e1n.",
    "clear_failed": "Nevymaz\u00e1no: {e}"
  },
  "de": {
    "title": "Aseko-Testf\u00e4lle",
    "last_frame": "Letzter Frame: {v}",
    "last_frame_ago": "Letzter Frame: vor <b>{s} s</b>",
    "last_frame_none": "Letzter Frame: noch keiner empfangen",
    "last_frame_error": "Letzter Frame: nicht verf\u00fcgbar ({e})",
    "placeholder": "Was wurde ge\u00e4ndert? z. B. Heizung EIN",
    "photo_mark": "Foto + Markierung",
    "mark": "Markieren",
    "wait": "auf n\u00e4chsten Frame warten",
    "intro": "Jede \u00c4nderung markieren; die F\u00e4lle jederzeit herunterladen.",
    "cases": "F\u00e4lle",
    "cases_count": "F\u00e4lle ({n}, nicht heruntergeladen: {f})",
    "no_cases": "Noch keine F\u00e4lle.",
    "download_new": "Neue herunterladen",
    "download_all": "Alle herunterladen",
    "clear": "Liste leeren",
    "downloaded": "heruntergeladen",
    "not_downloaded": "NICHT heruntergeladen",
    "frames_kept": "Frames vorhanden",
    "frames_gone": "Frames verfallen",
    "no_note": "(keine Notiz)",
    "photo": "Foto",
    "case_saved": "Fall #{n} gespeichert um {time}",
    "with_photo": " mit Foto",
    "uploading": "Foto wird hochgeladen\u2026 der Fall ist noch nicht gespeichert.",
    "photo_failed": "Foto nicht gespeichert: {e}",
    "waiting": "Warte auf den n\u00e4chsten Frame\u2026 der Fall ist noch nicht gespeichert, am Ger\u00e4t nichts \u00e4ndern.",
    "saving": "Fall wird gespeichert\u2026",
    "no_frame": "Kein Frame innerhalb von 60 s.\n{cases} ohne Frame.",
    "frame_received": " \u2014 Frame empfangen, weiter mit der n\u00e4chsten \u00c4nderung.",
    "mark_failed": "Fall nicht gespeichert: {e}",
    "zipping": "Zip wird erstellt\u2026",
    "zipped": "Zip heruntergeladen ({kb} kB).",
    "download_failed": "Download fehlgeschlagen: {e}",
    "clear_confirm": "Liste der F\u00e4lle leeren? Frames und Fotos bleiben in Home Assistant.",
    "cleared": "Liste geleert.",
    "clear_failed": "Nicht geleert: {e}"
  },
  "fr": {
    "title": "Cas de test Aseko",
    "last_frame": "Derni\u00e8re trame : {v}",
    "last_frame_ago": "Derni\u00e8re trame : il y a <b>{s} s</b>",
    "last_frame_none": "Derni\u00e8re trame : aucune re\u00e7ue",
    "last_frame_error": "Derni\u00e8re trame : indisponible ({e})",
    "placeholder": "Qu'avez-vous chang\u00e9 ? ex. Chauffage ON",
    "photo_mark": "Photo + marque",
    "mark": "Marquer",
    "wait": "attendre la trame suivante",
    "intro": "Marquez chaque changement ; t\u00e9l\u00e9chargez les cas quand vous voulez.",
    "cases": "Cas",
    "cases_count": "Cas ({n}, non t\u00e9l\u00e9charg\u00e9s : {f})",
    "no_cases": "Aucun cas pour l'instant.",
    "download_new": "T\u00e9l\u00e9charger les nouveaux",
    "download_all": "Tout t\u00e9l\u00e9charger",
    "clear": "Vider la liste",
    "downloaded": "t\u00e9l\u00e9charg\u00e9",
    "not_downloaded": "NON t\u00e9l\u00e9charg\u00e9",
    "frames_kept": "trames conserv\u00e9es",
    "frames_gone": "trames expir\u00e9es",
    "no_note": "(sans note)",
    "photo": "photo",
    "case_saved": "Cas #{n} enregistr\u00e9 \u00e0 {time}",
    "with_photo": " avec photo",
    "uploading": "Envoi de la photo\u2026 le cas n'est pas encore enregistr\u00e9.",
    "photo_failed": "Photo non enregistr\u00e9e : {e}",
    "waiting": "Attente de la trame suivante\u2026 le cas n'est pas encore enregistr\u00e9, ne touchez pas l'appareil.",
    "saving": "Enregistrement du cas\u2026",
    "no_frame": "Aucune trame en 60 s.\n{cases} sans trame.",
    "frame_received": " \u2014 trame re\u00e7ue, passez au changement suivant.",
    "mark_failed": "Cas non enregistr\u00e9 : {e}",
    "zipping": "Cr\u00e9ation du zip\u2026",
    "zipped": "Zip t\u00e9l\u00e9charg\u00e9 ({kb} ko).",
    "download_failed": "\u00c9chec du t\u00e9l\u00e9chargement : {e}",
    "clear_confirm": "Vider la liste des cas ? Les trames et photos restent dans Home Assistant.",
    "cleared": "Liste vid\u00e9e.",
    "clear_failed": "Non vid\u00e9e : {e}"
  }
};

const format = (text, values) => text.replace(/\{(\w+)\}/g, (_, key) => (values && key in values ? values[key] : `{${key}}`));

const esc = (text) =>
  String(text == null ? "" : text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class AsekoMarkCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._lang = this._lang || "en";
    this._thumbs = {};
    this._listKey = "";
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
    const lang = this._language(hass);
    if (lang !== this._lang) {
      this._lang = lang;
      this._listKey = "";
      if (this.shadowRoot) {
        this._render();
        this._poll();
      }
    }
  }

  _language(hass) {
    const wanted = this._config.language || (hass && ((hass.locale && hass.locale.language) || hass.language)) || "en";
    const base = String(wanted).toLowerCase().split(/[-_]/)[0];
    return STRINGS[base] ? base : "en";
  }

  _t(key, values) {
    const table = STRINGS[this._lang] || STRINGS.en;
    return format(table[key] || STRINGS.en[key] || key, values);
  }

  _locale() {
    return (this._hass && this._hass.locale && this._hass.locale.language) || this._lang;
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
    const title = this._config.title || this._t("title");
    const note = this.shadowRoot.getElementById && this.shadowRoot.getElementById("note");
    const draft = note ? note.value : "";
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
        <div class="age" id="age">${esc(this._t("last_frame", { v: "\u2026" }))}</div>
        <div class="row">
          <input id="note" type="text" placeholder="${esc(this._t("placeholder"))}" maxlength="200">
        </div>
        <div class="row">
          <button id="photo">\u{1F4F7} ${esc(this._t("photo_mark"))}</button>
          <button id="mark">\u{1F3C1} ${esc(this._t("mark"))}</button>
          <label><input id="wait" type="checkbox" checked> ${esc(this._t("wait"))}</label>
        </div>
        <input id="file" type="file" accept="image/*" capture="environment" hidden>
        <div class="status" id="status">${esc(this._t("intro"))}</div>
        <h3 id="heading">${esc(this._t("cases"))}</h3>
        <div class="cases" id="cases"><div class="empty">${esc(this._t("no_cases"))}</div></div>
        <div class="row">
          <button id="export-new">\u2B07 ${esc(this._t("download_new"))}</button>
          <button id="export-all" class="secondary">\u2B07 ${esc(this._t("download_all"))}</button>
          <button id="forget" class="secondary">${esc(this._t("clear"))}</button>
        </div>
      </ha-card>`;
    const $ = (id) => this.shadowRoot.getElementById(id);
    $("note").value = draft;
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
        ? this._t("last_frame_ago", { s: Math.round(Math.min(...ages)) })
        : esc(this._t("last_frame_none"));
      this._renderCases(data.entries);
    } catch (err) {
      this._el("age").textContent = this._t("last_frame_error", { e: err.message });
    }
  }

  _renderCases(entries) {
    const cases = entries.flatMap((e) => e.markers || []).sort((a, b) => b.n - a.n);
    const fresh = entries.reduce((sum, e) => sum + (e.not_downloaded || 0), 0);
    this._el("heading").textContent = this._t("cases_count", { n: cases.length, f: fresh });
    this._el("export-new").textContent = `\u2B07 ${this._t("download_new")} (${fresh})`;
    const key = JSON.stringify(cases.map((c) => [c.n, c.downloaded, c.frames, c.photo]));
    if (key === this._listKey) return;
    this._listKey = key;
    const list = this._el("cases");
    if (!cases.length) {
      list.innerHTML = `<div class="empty">${esc(this._t("no_cases"))}</div>`;
      return;
    }
    list.innerHTML = cases
      .map((c) => {
        const when = new Date(c.t).toLocaleString(this._locale());
        const flags = [
          this._t(c.downloaded ? "downloaded" : "not_downloaded"),
          this._t(c.frames ? "frames_kept" : "frames_gone"),
        ].join(" \u00B7 ");
        const img = c.photo ? `<img data-photo="${esc(c.photo)}" alt="${esc(this._t("photo"))}">` : "";
        return `<div class="case ${c.downloaded ? "" : "new"}">${img}
          <div class="txt"><div class="note">#${c.n} ${esc(c.note || this._t("no_note"))}</div>
          <div class="meta">${esc(when)} \u00B7 ${esc(flags)}</div></div></div>`;
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
      .map((m) => this._t("case_saved", { n: m.marker, time: new Date(m.time).toLocaleTimeString(this._locale()) }) + (extra || ""))
      .join("\n");
  }

  async _upload(input) {
    const file = input.files && input.files[0];
    input.value = "";
    if (!file) return;
    this._busy(true);
    this._setStatus(this._t("uploading"), "waiting");
    try {
      const form = new FormData();
      form.append("note", this._note());
      form.append("photo", file, file.name || "photo.jpg");
      const response = await this._hass.fetchWithAuth(PHOTO_URL, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
      this._setStatus(this._describe(data.markers, this._t("with_photo")), "done");
      this._el("note").value = "";
      this._poll();
    } catch (err) {
      this._setStatus(this._t("photo_failed", { e: err.message }), "error");
    } finally {
      this._busy(false);
    }
  }

  async _mark() {
    const wait = this._el("wait").checked;
    this._busy(true);
    this._setStatus(
      this._t(wait ? "waiting" : "saving"),
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
          ? this._t("no_frame", { cases: this._describe(markers) })
          : this._describe(markers) + (wait ? this._t("frame_received") : ""),
        late ? "error" : "done",
      );
      this._el("note").value = "";
      this._poll();
    } catch (err) {
      this._setStatus(this._t("mark_failed", { e: err.message }), "error");
    } finally {
      this._busy(false);
    }
  }

  async _export(onlyNew) {
    this._busy(true);
    this._setStatus(this._t("zipping"), "waiting");
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
      this._setStatus(this._t("zipped", { kb: Math.round(blob.size / 1024) }), "done");
      this._poll();
    } catch (err) {
      this._setStatus(this._t("download_failed", { e: err.message }), "error");
    } finally {
      this._busy(false);
    }
  }

  async _forget() {
    if (!window.confirm(this._t("clear_confirm"))) return;
    this._busy(true);
    try {
      const response = await this._hass.fetchWithAuth(FORGET_URL, { method: "POST" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      this._setStatus(this._t("cleared"), "done");
      this._poll();
    } catch (err) {
      this._setStatus(this._t("clear_failed", { e: err.message }), "error");
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
