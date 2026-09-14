/*
 * Aseko test cases card: mark test cases in the frame log, photograph the unit's
 * display, and download everything later from any device.
 *
 *   type: custom:aseko-test-cases-card
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

class AsekoTestCasesCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._lang = this._lang || "en";
    this._pruneThumbs(null);
    this._thumbs = {};
    this._listKey = "";
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this._render();
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
    clearInterval(this._timer);
    this._timer = setInterval(() => this._poll(), 3000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    this._pruneThumbs(null);
    this._listKey = "";
  }

  _render() {
    const title = this._config.title || this._t("title");
    const note = this.shadowRoot.getElementById && this.shadowRoot.getElementById("note");
    const draft = note ? note.value : "";
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --aseko-accent: var(--primary-color, #2b87ff);
          --aseko-accent-soft: color-mix(in srgb, var(--aseko-accent) 12%, transparent);
          --aseko-surface: color-mix(in srgb, var(--primary-text-color) 4%, var(--card-background-color));
          --aseko-border: color-mix(in srgb, var(--primary-text-color) 12%, transparent);
          display: block;
        }
        * { box-sizing: border-box; }
        ha-card {
          container-type: inline-size;
          overflow: hidden;
          border-radius: var(--ha-card-border-radius, 16px);
          background: var(--ha-card-background, var(--card-background-color));
        }
        .hero {
          position: relative;
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 20px 22px 18px;
          border-bottom: 1px solid var(--aseko-border);
          background:
            radial-gradient(circle at 92% -20%, color-mix(in srgb, var(--aseko-accent) 22%, transparent), transparent 52%),
            linear-gradient(135deg, color-mix(in srgb, var(--aseko-accent) 8%, transparent), transparent 58%);
        }
        .brand-icon {
          display: grid;
          width: 44px;
          height: 44px;
          flex: 0 0 44px;
          place-items: center;
          border-radius: 14px;
          color: var(--aseko-accent);
          background: var(--aseko-accent-soft);
          box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aseko-accent) 20%, transparent);
        }
        .brand-icon ha-icon { --mdc-icon-size: 26px; }
        .hero-copy { min-width: 0; flex: 1; }
        h2 { margin: 0; color: var(--primary-text-color); font-size: 1.22rem; font-weight: 700; line-height: 1.25; }
        .age {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          margin-top: 5px;
          color: var(--secondary-text-color);
          font-size: .84rem;
          line-height: 1.3;
        }
        .age::before {
          width: 8px;
          height: 8px;
          flex: 0 0 8px;
          border-radius: 50%;
          background: var(--disabled-text-color);
          content: "";
          box-shadow: 0 0 0 3px color-mix(in srgb, var(--disabled-text-color) 16%, transparent);
        }
        .age[data-state="fresh"]::before { background: var(--success-color, #43a047); box-shadow: 0 0 0 3px color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); }
        .age[data-state="stale"]::before { background: var(--warning-color, #f0a000); box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning-color, #f0a000) 18%, transparent); }
        .age[data-state="error"]::before { background: var(--error-color, #db4437); box-shadow: 0 0 0 3px color-mix(in srgb, var(--error-color, #db4437) 18%, transparent); }
        .age b { color: var(--primary-text-color); font-size: 1em; font-weight: 700; }
        .body { padding: 20px 22px 22px; }
        .composer {
          padding: 14px;
          border: 1px solid var(--aseko-border);
          border-radius: 15px;
          background: var(--aseko-surface);
        }
        .input-wrap { position: relative; }
        .input-wrap ha-icon {
          position: absolute;
          top: 50%;
          left: 13px;
          color: var(--secondary-text-color);
          pointer-events: none;
          transform: translateY(-50%);
          --mdc-icon-size: 20px;
        }
        input[type=text] {
          width: 100%;
          min-width: 0;
          height: 46px;
          padding: 0 14px 0 42px;
          border: 1px solid var(--aseko-border);
          border-radius: 11px;
          outline: none;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font: inherit;
          transition: border-color .18s ease, box-shadow .18s ease;
        }
        input[type=text]::placeholder { color: var(--secondary-text-color); opacity: .82; }
        input[type=text]:focus { border-color: var(--aseko-accent); box-shadow: 0 0 0 3px var(--aseko-accent-soft); }
        .action-row { display: flex; align-items: center; gap: 9px; margin-top: 10px; }
        button {
          display: inline-flex;
          min-height: 42px;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 0 15px;
          border: 1px solid transparent;
          border-radius: 11px;
          outline: none;
          background: var(--aseko-accent);
          color: var(--text-primary-color, #fff);
          font: inherit;
          font-size: .92rem;
          font-weight: 650;
          cursor: pointer;
          transition: transform .15s ease, filter .15s ease, box-shadow .15s ease;
        }
        button:hover:not(:disabled) { filter: brightness(1.06); box-shadow: 0 4px 12px color-mix(in srgb, var(--aseko-accent) 22%, transparent); transform: translateY(-1px); }
        button:active:not(:disabled) { transform: translateY(0); }
        button:focus-visible { box-shadow: 0 0 0 3px var(--card-background-color), 0 0 0 5px var(--aseko-accent); }
        button ha-icon { --mdc-icon-size: 19px; }
        button.secondary { border-color: var(--aseko-border); background: transparent; color: var(--primary-text-color); }
        button.secondary:hover:not(:disabled) { background: var(--aseko-surface); box-shadow: none; }
        button.danger { color: var(--error-color, #db4437); }
        button:disabled { opacity: .46; cursor: not-allowed; }
        .wait-option {
          display: flex;
          min-height: 42px;
          align-items: center;
          gap: 8px;
          margin-left: auto;
          color: var(--secondary-text-color);
          font-size: .84rem;
          cursor: pointer;
          user-select: none;
        }
        .wait-option input { width: 17px; height: 17px; margin: 0; accent-color: var(--aseko-accent); }
        .status {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          margin-top: 11px;
          padding: 10px 12px;
          border-radius: 10px;
          background: color-mix(in srgb, var(--secondary-text-color) 8%, transparent);
          color: var(--secondary-text-color);
          font-size: .86rem;
          line-height: 1.4;
          white-space: pre-line;
        }
        .status::before { flex: 0 0 auto; content: "ⓘ"; font-weight: 700; }
        .status.waiting { background: color-mix(in srgb, var(--warning-color, #f0a000) 14%, transparent); color: var(--primary-text-color); }
        .status.waiting::before { content: "⏳"; }
        .status.done { background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent); color: var(--primary-text-color); }
        .status.done::before { color: var(--success-color, #43a047); content: "✓"; }
        .status.error { background: color-mix(in srgb, var(--error-color, #db4437) 14%, transparent); color: var(--primary-text-color); }
        .status.error::before { color: var(--error-color, #db4437); content: "!"; }
        .history { margin-top: 22px; }
        .section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 9px; }
        h3 { margin: 0; color: var(--primary-text-color); font-size: .98rem; font-weight: 700; }
        .cases { display: flex; flex-direction: column; gap: 8px; }
        .case {
          position: relative;
          display: flex;
          min-width: 0;
          align-items: center;
          gap: 12px;
          padding: 11px 12px;
          border: 1px solid var(--aseko-border);
          border-radius: 13px;
          background: var(--card-background-color);
        }
        .case.new { border-color: color-mix(in srgb, var(--warning-color, #f0a000) 40%, var(--aseko-border)); background: color-mix(in srgb, var(--warning-color, #f0a000) 5%, var(--card-background-color)); }
        .case.new::before { position: absolute; inset: 10px auto 10px 0; width: 3px; border-radius: 0 3px 3px 0; background: var(--warning-color, #f0a000); content: ""; }
        .case img { width: 58px; height: 58px; flex: 0 0 58px; object-fit: cover; border-radius: 10px; cursor: zoom-in; }
        .case-number {
          display: grid;
          width: 34px;
          height: 34px;
          flex: 0 0 34px;
          place-items: center;
          border-radius: 10px;
          background: var(--aseko-accent-soft);
          color: var(--aseko-accent);
          font-size: .78rem;
          font-weight: 800;
        }
        .case .txt { min-width: 0; flex: 1; }
        .case .note { overflow-wrap: anywhere; color: var(--primary-text-color); font-size: .93rem; font-weight: 650; line-height: 1.35; }
        .case .meta { margin-top: 3px; color: var(--secondary-text-color); font-size: .77rem; line-height: 1.35; }
        .case-flags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
        .flag { padding: 3px 7px; border-radius: 999px; background: var(--aseko-surface); color: var(--secondary-text-color); font-size: .68rem; font-weight: 650; }
        .flag.new { background: color-mix(in srgb, var(--warning-color, #f0a000) 15%, transparent); color: color-mix(in srgb, var(--warning-color, #f0a000) 72%, var(--primary-text-color)); }
        .empty {
          display: grid;
          min-height: 104px;
          place-items: center;
          padding: 20px;
          border: 1px dashed var(--aseko-border);
          border-radius: 13px;
          color: var(--secondary-text-color);
          text-align: center;
          font-size: .88rem;
        }
        .footer-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
        .footer-actions .danger { margin-left: auto; }
        .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
        @container (max-width: 560px) {
          .hero { padding: 17px 16px 15px; }
          .body { padding: 16px; }
          .composer { padding: 12px; }
          .action-row { align-items: stretch; flex-wrap: wrap; }
          .action-row button { flex: 1 1 calc(50% - 5px); padding-inline: 10px; }
          .wait-option { width: 100%; min-height: 32px; margin-left: 2px; }
          .footer-actions button { flex: 1 1 calc(50% - 4px); padding-inline: 10px; }
          .footer-actions .danger { flex-basis: 100%; margin-left: 0; }
          .case { align-items: flex-start; }
          .case-number { display: none; }
          .case img { width: 52px; height: 52px; flex-basis: 52px; }
        }
        @media (prefers-reduced-motion: reduce) { button, input { transition: none; } }
      </style>
      <ha-card>
        <header class="hero">
          <div class="brand-icon" aria-hidden="true"><ha-icon icon="mdi:pool"></ha-icon></div>
          <div class="hero-copy">
            <h2>${esc(title)}</h2>
            <div class="age" id="age" data-state="unknown">${esc(this._t("last_frame", { v: "\u2026" }))}</div>
          </div>
        </header>
        <div class="body">
          <section class="composer">
            <label class="sr-only" for="note">${esc(this._t("placeholder"))}</label>
            <div class="input-wrap">
              <ha-icon icon="mdi:text-box-edit-outline" aria-hidden="true"></ha-icon>
              <input id="note" type="text" placeholder="${esc(this._t("placeholder"))}" maxlength="200" autocomplete="off">
            </div>
            <div class="action-row">
              <button id="photo"><ha-icon icon="mdi:camera-plus-outline" aria-hidden="true"></ha-icon>${esc(this._t("photo_mark"))}</button>
              <button id="mark" class="secondary"><ha-icon icon="mdi:flag-checkered" aria-hidden="true"></ha-icon>${esc(this._t("mark"))}</button>
              <label class="wait-option"><input id="wait" type="checkbox" checked> ${esc(this._t("wait"))}</label>
            </div>
            <input id="file" type="file" accept="image/*" capture="environment" hidden>
            <div class="status" id="status" role="status" aria-live="polite">${esc(this._t("intro"))}</div>
          </section>
          <section class="history">
            <div class="section-heading"><h3 id="heading">${esc(this._t("cases"))}</h3></div>
            <div class="cases" id="cases"><div class="empty">${esc(this._t("no_cases"))}</div></div>
            <div class="footer-actions">
              <button id="export-new"><ha-icon icon="mdi:download-outline" aria-hidden="true"></ha-icon>${esc(this._t("download_new"))}</button>
              <button id="export-all" class="secondary"><ha-icon icon="mdi:archive-arrow-down-outline" aria-hidden="true"></ha-icon>${esc(this._t("download_all"))}</button>
              <button id="forget" class="secondary danger"><ha-icon icon="mdi:delete-sweep-outline" aria-hidden="true"></ha-icon>${esc(this._t("clear"))}</button>
            </div>
          </section>
        </div>
      </ha-card>`;
    const $ = (id) => this.shadowRoot.getElementById(id);
    $("note").value = draft;
    $("photo").addEventListener("click", () => $("file").click());
    $("file").addEventListener("change", (ev) => this._upload(ev.target));
    $("mark").addEventListener("click", () => this._mark());
    $("note").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && !ev.isComposing) {
        ev.preventDefault();
        this._mark();
      }
    });
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
    this._el("note").disabled = busy;
    this._el("wait").disabled = busy;
    this._el("status").setAttribute("aria-busy", String(busy));
  }

  async _poll() {
    if (!this._hass || !this.shadowRoot) return;
    try {
      const response = await this._hass.fetchWithAuth(STATUS_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const ages = data.entries.flatMap((e) => Object.values(e.seconds_since_last_frame));
      const youngest = ages.length ? Math.min(...ages) : null;
      this._el("age").innerHTML = ages.length
        ? this._t("last_frame_ago", { s: Math.round(youngest) })
        : esc(this._t("last_frame_none"));
      this._el("age").dataset.state = youngest == null ? "unknown" : youngest <= 15 ? "fresh" : "stale";
      this._renderCases(data.entries);
    } catch (err) {
      this._el("age").textContent = this._t("last_frame_error", { e: err.message });
      this._el("age").dataset.state = "error";
    }
  }

  _renderCases(entries) {
    // Marker numbers count per config entry, so order by time and keep the
    // entry each case came from.
    const cases = entries
      .flatMap((e) => (e.markers || []).map((m) => ({ ...m, entry: e.entry, entryId: e.entry_id })))
      .sort((a, b) => new Date(b.t) - new Date(a.t) || b.n - a.n);
    const several = entries.length > 1;
    const fresh = entries.reduce((sum, e) => sum + (e.not_downloaded || 0), 0);
    this._el("heading").textContent = this._t("cases_count", { n: cases.length, f: fresh });
    this._el("export-new").textContent = `\u2B07 ${this._t("download_new")} (${fresh})`;
    const key = JSON.stringify([several, cases.map((c) => [c.entryId, c.n, c.t, c.note, c.downloaded, c.frames, c.photo])]);
    this._pruneThumbs(new Set(cases.map((c) => c.photo).filter(Boolean)));
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
        const downloadFlag = this._t(c.downloaded ? "downloaded" : "not_downloaded");
        const framesFlag = this._t(c.frames ? "frames_kept" : "frames_gone");
        const img = c.photo ? `<img data-photo="${esc(c.photo)}" alt="${esc(this._t("photo"))}">` : "";
        return `<article class="case ${c.downloaded ? "" : "new"}">${img}
          <div class="case-number" aria-hidden="true">#${c.n}</div>
          <div class="txt"><div class="note">${esc(c.note || this._t("no_note"))}</div>
          <div class="meta">#${c.n} \u00B7 ${esc(when)}${several ? ` \u00B7 ${esc(c.entry)}` : ""}</div>
          <div class="case-flags"><span class="flag ${c.downloaded ? "" : "new"}">${esc(downloadFlag)}</span><span class="flag">${esc(framesFlag)}</span></div></div></article>`;
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
    const pending = this._thumbs[name];
    const url = await pending;
    if (!url && this._thumbs[name] === pending) delete this._thumbs[name]; // try again next render
    if (url) {
      img.src = url;
      img.onclick = () => window.open(url, "_blank");
    }
  }

  _pruneThumbs(keep) {
    for (const [name, pending] of Object.entries(this._thumbs || {})) {
      if (keep && keep.has(name)) continue;
      delete this._thumbs[name];
      pending.then((url) => url && URL.revokeObjectURL(url));
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

if (!customElements.get("aseko-test-cases-card")) {
  customElements.define("aseko-test-cases-card", AsekoTestCasesCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "aseko-test-cases-card",
    name: "Aseko test cases",
    description: "Mark test cases in the Aseko frame log, photograph the unit's display and download them from any device.",
  });
}
