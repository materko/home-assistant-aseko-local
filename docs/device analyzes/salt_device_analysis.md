# ASIN AQUA Salt – Reverse Engineering & Implementation Notes

## Device

| Field | Value |
|---|---|
| Model | ASIN AQUA Salt |
| Firmware | 5.x – 7.x |
| Source | PR #87 live captures 2026-04-04; earlier frames 2026-04-02, 2026-04-03; Issue #84; maintainer's two units (one REDOX, one CLF), 37 diagnostics downloads Aug 2026, an app + display review 2026-09-11, and test cases marked in the frame log on the REDOX unit 2026-09-13/14 (one setting changed at a time, a marker after the next frame) |
| byte[4] | `0x0E` (Redox) or `0x0D` (CLF) or `0x0f` (DOSE) → `(data[4] & 0x0C) == 0x0C` → **SALT** |

---

## Frame Structure

All SALT frames are 120 bytes, split into three 40-byte sub-frames. The sub-frame type is
encoded at byte offset 5 (first sub-frame), 45, and 85:

| Sub-frame | Type byte | Content |
|---|---|---|
| 0–39 | `0x01` | Live sensor data |
| 40–79 | `0x03` | Configuration / setpoints |
| 80–119 | `0x02` | Flow rates / dosing |

---

## byte[4] – Unit Type Detection

`UNIT_TYPE_SALT = 0x0C`. Detection: `(data[4] & 0x0C) == 0x0C`.

Known values observed: `0x0D`, `0x0E`. Both match the SALT mask.

**Convention**: **Bit SET (`1`) = probe ABSENT; bit CLEAR (`0`) = probe PRESENT** (negative/inverted
convention, named `PROBE_X_MISSING` in the code).

| Bit | Mask | Constant | Bit SET (1) means | Bit CLEAR (0) means |
|---|---|---|---|---|
| 0 | `0x01` | `PROBE_REDOX_MISSING` | REDOX probe **absent** | REDOX probe **present** |
| 1 | `0x02` | `PROBE_CLF_MISSING` | CLF probe **absent** | CLF probe **present** |
| 2–3 | `0x0C` | `UNIT_TYPE_SALT` | **SALT type identifier** (both bits must be set) | — |

---

## Byte Map – Sub-frame 1 (live sensor data)

| Byte(s) | Decoded | Notes |
|---|---|---|
| `[0:4]` | Serial number (big-endian) | |
| `[4]` | Unit type + probe flags | `0x0E` or `0x0D` |
| `[5]` | Sub-frame type `0x01` | |
| `[6:12]` | Timestamp (year−2000, month, day, hour, min, sec) | Device clock |
| `[12]` | Dosing-warning bitmask | Usually `0x00` on SALT — see [`home_device_analysis.md`](home_device_analysis.md) §"Dosing warnings & alarms" |
| `[13]` | Alarm bitmask | `0x04` = no flow to probes; see § above |
| `[14:16]` | pH = value / 100 | |
| `[16:18]` | CLF or REDOX (probe-dependent) | CLF: `/100` mg/L; REDOX: `×1` mV |
| `[18:20]` | REDOX (if CLF also present on PROFI-style) | Not applicable on basic SALT |
| `[20]` | Salinity = value / 10 | SALT-specific |
| `[21]` | Electrolyzer power (% or raw) | `0` when electrolyzer not running |
| `[22]` | Settings flags | **See §byte[22]** |
| `[23:25]` | Air temperature = signed value / 10 | °C — see §Air temperature |
| `[25:27]` | Water temperature = value / 10 | °C |
| `[28]` | Water flow to probes | `0xAA` = flowing |
| `[29]` | Actuator bitmask | **See §byte[29]** |
| `[37]` | Settings flags: menu, filtration periods, heating control, waterlevel, flow detection, third-pump routing | **See §byte[37]** |

---

## Air temperature — byte `[23:25]`

Bytes 23-24 hold the air (ambient) temperature as a 16-bit big-endian two's
complement value, `value / 10` = °C — the same encoding as the water
temperature that follows it in bytes 25-26. The field was previously listed as
"unknown".

**Evidence** — two diagnostics dumps from an ASIN AQUA Salt (
type byte `0x0d`), both matching the readings shown on the unit:

| Captured | Bytes 23-24 | Air | Bytes 25-26 | Water |
|---|---|---|---|---|
| 2026-08-11 10:33 | `0x0168` = 360 | 36.0 °C | `0x0128` = 296 | 29.6 °C |
| 2026-08-17 18:50 | `0x0134` = 308 | 30.8 °C | `0x0122` = 290 | 29.0 °C |

Both fields move independently, and each raw air value occurs exactly once in
its 120-byte frame, so the offset is unambiguous. Byte 22 stayed `0x18` in both
samples, so this is a plain 16-bit field and not the low half of a 24-bit one.

**Signedness.** Read unsigned, frames from units without an air probe decode to
6513.6 °C (`0xFE70`) and 6502.8 °C (`0xFDC4`); as two's complement the same
bytes read -40.0 °C and -57.2 °C, i.e. an open-circuit temperature input. The
decoder therefore reads the field signed and discards anything outside
-30.0 … 60.0 °C, which filters both sentinels. A genuine sub-zero reading has
not been captured yet, so the cold-weather encoding remains unverified.

`0xFFFF` is rejected up front as the protocol-wide "unspecified" marker — read
signed it would otherwise pass the window as -0.1 °C.

**Scope.** Confirmed on SALT only. The HOME and OXY profiles list air temperature too — the Aseko Live
app and the manuals show it on those models — but every captured HOME and OXY frame carries the
open-circuit value, so the reading is NOT_PRESENT there and no entity appears until a probe is fitted.
NET is left out: it carries unrelated data in these bytes (e.g. `0x0C3C` = 313.2 °C).

## byte[29] – Actuator Bitmask

| Bit | Mask | Meaning | Evidence |
|---|---|---|---|
| 0 | `0x01` | Backwash valve open | ✅ capture of a manual backwash, 2026-08-11 |
| 1 | `0x02` | Refilling (water filling valve) | ✅ 2026-09-06: set when the level fell to the refill start threshold, cleared at the refill stop threshold |
| 3 | `0x08` | Filtration running | ✅ every active phase (PR #87) |
| 4 | `0x10` | Electrolysis running | ✅ 25 frames (PR #87) |
| 5 | `0x20` | Algicide / flocculant pump (the shared third port) | ✅ 27 frames (PR #87) |
| 6 | `0x40` | Electrode polarity: **set = right, clear = left** | ✅ polarity switched by hand both ways, 2026-09-13 |
| 7 | `0x80` | pH− pump | ⏳ never set in a captured SALT frame |

The polarity bit only means something while `0x10` is set; with electrolysis stopped the polarity
reads *waiting*. Earlier notes had it the other way round (`0x50` = left, from one April frame); the
by-hand switch settled it, and the decoder was corrected.

Algicide and flocculant share **the same bit `0x20`**: the third pump port is a single physical
output, and `byte[37]` says which chemical it doses. The electrolyser and the third pump can run at
the same time.

---

## byte[37] – Third-Pump Routing (Algicide vs. Flocculant)

The SALT unit has one physical pump port that can be configured as either algicide or
flocculant. `byte[37]` encodes which chemical is active:

| byte[37] value | bit 7 | Chemical configured |
|---|---|---|
| `0xb7`, `0xb3` | `1` | **Algicide** (ml/m³/day) |
| `0x37` | `0` | **Flocculant** (ml/h) |
| `0xFF` | N/A | Not configured / NET device |

**Routing rule (Hopkins firmware v7.x)**: `byte[37] & 0x80 == 0x80` → algicide; else → flocculant.

### Firmware variant caution

Issue #84 SALT shows `byte[37] = 0x13` for algicide. Here bit 7 (`0x80`) is **not** set —
the routing bit differs from the v7.x firmware. The two SALT variants encode the chemical
type differently in byte[37].

**Implication**: the `0x80` routing rule is not universally reliable across all SALT
firmware versions. See [byte37_algicide_floc_analysis.md](../temp/byte37_algicide_floc_analysis.md) for
full XOR analysis.

**Note on Period 2 schedule bytes (Issue #133)**: On SALT, the controller keeps
sending the last-configured `start2`/`stop2` times in bytes 60-63 even after
the user disables Period 2 in the controller UI.  Pre-fix, the decoder
gated these fields on `byte[37] & 0x80` and returned `None` for any frame
where the algicide-routing bit was clear — which caused already-registered
entities to flip to "unknown" when the user toggled Period 2 on/off
(Home Assistant protects the entity registry, so the entity stays but
the value is read as `None`).  Post-fix, bytes 60-63 are read
unconditionally on every model with a filtration output (SALT included), and
the mode and schedule are decoded from the `byte[37]` bits (see
§byte[37] – filtration mode and schedule below).  Behaviour was originally verified on SALT by
diffing two frames
captured in PR #122 (algicide mode toggle, `0xb3` ↔ `0x33`); the
corresponding behaviour for HOME was confirmed in Issue #133 with
@dtpugh's four diagnostic files (see
[`home_device_analysis.md`](home_device_analysis.md) §"Note on Period 2
schedule bytes (Issue #133)").  NET is excluded because it has no
filtration output.

### byte[37] also contains other fields

`byte[37]` is a packed multi-field byte — it is **not** a pure single-bit flag:

| Comparison | XOR | Bit(s) changed |
|---|---|---|
| Algicide 10 → Algicide 11 (dosage +1) | `0x04` | bit 2 only |
| Algicide 11 → Flocculant 11 (type change) | `0x84` | bit 7 + bit 2 |
| Algicide 10 → Flocculant 11 (both change) | `0x80` | bit 7 only |

Bit 2 (`0x04`) was read here as dosage encoding.  **That reading is
superseded**: `0x04` marks the unit's settings menu, captured directly on an ASIN
AQUA Salt across six byte[37] values and both directions of every transition
(see §byte[37] – filtration mode and schedule below).  The XOR above came
from two frames diffed in PR #122; the dosage change and a mode change most
likely coincided in that pair.  The remaining bits are unconfirmed.

### byte[37] – filtration mode and schedule

`byte[37]` carries **two independent facts** about filtration, and the decoder
keeps them apart because neither can stand in for the other:

| Bits | Meaning | Field |
|---|---|---|
| `0x10` / `0x20` | which schedule is configured | `filtration_schedule` |
| `0x04` | the unit's settings menu is open | `service_menu_open` |

Every combination below was captured on an ASIN AQUA Salt with the mode shown
on the unit itself known, in both directions of each transition:

| `byte[37]` | `service_menu_open` | `filtration_schedule` |
|---|---|---|
| `0xC3` | `False` | `NONSTOP_24H` |
| `0xD3` | `False` | `TIMER_PERIOD_1` |
| `0xF3` | `False` | `TIMER_PERIOD_1_AND_2` |
| `0xC7` | `True` | `NONSTOP_24H` |
| `0xD7` | `True` | `TIMER_PERIOD_1` |
| `0xF7` | `True` | `TIMER_PERIOD_1_AND_2` |

These are the same mode bits HOME uses. The high nibble is SALT's configuration: `0x80` is the
algicide routing, `0x40` the Waterlevel setting (see §byte[37] – the whole byte).

The filtration times in bytes 56-63 are reported unchanged in every mode, so the mode can only come
from these bits, never from the times.

**What the bit actually marks.** `0x04` appears the moment the settings menu
is opened on the unit — the menu holding every Aseko setting, and the place
filtration and backwash can be started by hand from.  It is set **before**
anything is touched: three captures labelled "switched to manual mode, did
nothing" carry it.  So on its own the bit says a person is standing at the
unit, and nothing about what they did.

**The unit goes quiet while the menu is open.** Opening it produces exactly
one more frame — the one carrying `0x04` — and then transmission stops until
the user leaves.  Three diagnostics taken during one such session all
contained the same frame, with `online` going false between them.  Two
consequences:

* `service_menu_open` going True is typically the last thing reported before
  the device goes offline, and it stays True until the user comes back out.
  This is correct — it is the last thing the unit actually said.
* What the user *does* in there is not observable.  The pump state in that
  final frame is the state on the way in, not the result.  The unit will not
  let you leave until filtration is back in the state it was in before, so
  the value Home Assistant is holding is right again by the time frames
  resume.

Note this is **not** evidence that the schedule is suspended while the menu
is open: in the 2026-08-11 capture the pump kept running throughout, and the
configured period 1 covered that time of day anyway.

The exception is a by-hand **backwash**: there the unit keeps transmitting
throughout, with `0x04` set from ~30 s before the valve opens until ~20 s
after it closes.  A cycle running while somebody is at the menu the button
lives on is manual by observation, and `trackers.backwash` uses it as such
rather than inferring from the clock — see `_service_menu_open`.

### byte[37] – the whole byte

Toggling one setting at a time on the unit (2026-09-13) mapped every bit:

| Bit | Mask | Meaning | Field |
|---|---|---|---|
| 0 | `0x01` | always set | — |
| 1 | `0x02` | Flow detection enabled | `flow_detection_enabled` |
| 2 | `0x04` | settings menu open | `service_menu_open` |
| 3 | `0x08` | Heating control enabled | `heating_control_enabled` |
| 4 | `0x10` | filtration period 1 enabled | `filtration_schedule` |
| 5 | `0x20` | filtration period 2 enabled | `filtration_schedule` |
| 6 | `0x40` | Waterlevel (level meter) enabled; winter mode clears it | `water_level_sensor_enabled` |
| 7 | `0x80` | third port doses algicide (clear = flocculant) | routing of `algaecide_*` / `flocculant_*` |

These are **settings, not hardware**: Waterlevel, Heating control or the VS pump can be switched on
without the sensor, the heater or the pump connected, and the app then simply shows nothing for it.

Bit `0x40` is the bit the decoder once took for a HOME "firmware A / B" split. It is a setting, the
same on HOME and SALT, so HOME has one profile now (see `home_device_analysis.md`).

---

## byte[22] – settings flags

| Bit | Mask | Meaning | Field |
|---|---|---|---|
| 0 | `0x01` | heating only inside its time window | `heating_condition` = `time_window` |
| 1 | `0x02` | heating by outside temperature | `heating_condition` = `outside_temperature_above` / `_below` |
| 2 | `0x04` | Winter mode on | `freeze_protection_enabled` |
| 3 | `0x08` | VS pump enabled (the setting, not the pump running) | `variable_speed_pump_enabled` |
| 4 | `0x10` | backwash schedule enabled | `backwash_schedule_enabled` |
| 5 | `0x20` | with `0x02`: heat when **below** the outside temperature (clear = above) | `heating_condition` |

`0x01` and `0x02` were never set together; `heating_condition` is `always` when neither is set.

## byte[78] – live state and VS pump type

| Bits | Meaning | Field |
|---|---|---|
| `0x80` | heating allowed right now: follows the time window and the outside-temperature condition as the clock and the settings change | `heating_allowed` |
| `0x40` | winter mode active | — (same as `byte[22]` 0x04) |
| `0x0C` | VS pump type: `0x00` Speck / Uwe EO PM, `0x04` Pentair / Dab E.SWIM, `0x08` Hayward. The type is kept while the VS pump is switched off, and changes immediately when another pump is picked | `variable_speed_pump_type` |
| `0x02` / `0x01` | follow the filtration state: `0x02` while filtration runs, `0x01` while it stands (both or neither only in transitions). Seen the same way on NET and OXY frames | not decoded — `byte[29]` 0x08 says the same |

## Winter mode

Switching winter mode on (2026-09-13, twice):

- `byte[22]` 0x04 and `byte[78]` 0x40 set, `byte[37]` 0x40 cleared (level control off);
- the setpoint bytes carry the **winter program** instead of the normal settings while it is on:
  `byte[54]` algicide 2 ml, `byte[55]` water 2 °C, bytes 56-59 filtration 12:00–12:15, bytes 60-63
  18:00–22:00, `byte[68]` backwash 0 (off); the normal values return when winter mode is switched off;
- filtration runs for about 15–20 s right after switching it on (`byte[29]` 0x08, `byte[78]` 0x02).

## Settings the frame does not carry

Changed on the unit with a marker after the next frame, and no byte moved:
the heating time window (start / end), the outside-temperature threshold, the electrode polarity
switching interval (1 h / 24 h / 7 days / manual), the programmable relay and its periods, and the
display language.

Settings that did move: `byte[112]` pH− concentration (15 → 21 % on the unit), `byte[115]` max. pH
doses (17 → 20), `byte[55]` water temperature target (25 → 15 °C).

Still open: `byte[38]` bit `0x10` was set while *heating control is parent to filtration* was
switched on, but the same session changed other heating settings, and `byte[38]` also takes values
(`0x20`, `0xA1`, `0x01`) around the winter-mode switch — it needs a clean test of that one setting.

---

## Byte Map – Sub-frame 2 (config / setpoints)

| Byte(s) | Decoded | Notes |
|---|---|---|
| `[52]` | Required pH = value / 10 | |
| `[53]` | Required CLF (mg/L ÷10) or REDOX (×10 mV) | Depends on active probe |
| `[54]` | Required algicide (ml/m³/day) or Required floc (ml/h) | Routed by `byte[37]` |
| `[55]` | Required water temperature (°C) | Winter program value while winter mode is on |
| `[56:58]` | Filtration start1 | HH:MM |
| `[58:60]` | Filtration stop1 | HH:MM |
| `[60:62]` | Filtration start2 | HH:MM | Always populated — see Issue #133 |
| `[62:64]` | Filtration stop2 | HH:MM | Always populated — see Issue #133 |
| `[68]` | Backwash every N days | `0` = disabled |
| `[69:71]` | Backwash time | HH:MM |
| `[71]` | Backwash duration | ×10 seconds |
| `[76:78]` | Max. refill time (s) | |
| `[78]` | Heating allowed, winter active, VS pump type | **See §byte[78]** |

---

## Byte Map – Sub-frame 3 (flow rates)

| Byte(s) | Decoded | Notes |
|---|---|---|
| `[92:94]` | Pool volume (m³) | |
| `[95]` | Flowrate pH− (ml/min) | Confirmed |
| `[99]` | Flowrate chlorine pump (ml/min) | Not applicable on SALT (no CL pump) |
| `[101]` | Flowrate third-pump slot (ml/min) | 60 ml/min in all captured frames |
| `[103]` | Flowrate third-pump slot (duplicate?) | Also 60 ml/min; does not flip with algicide/floc switch |

**Note on byte[101] vs byte[103]**: Both bytes carry the same flowrate (60 ml/min)
regardless of whether algicide or flocculant is configured. The third pump slot does NOT
split its flowrate across different bytes when switching chemicals — see
[byte37_algicide_floc_analysis.md](../temp/byte37_algicide_floc_analysis.md).

---

## Electrolyzer

The SALT unit has an integrated salt-water electrolysis cell for chlorine production.

| Field | byte | Notes |
|---|---|---|
| `electrolysis_running` | `[29] & 0x10` | `True` when RIGHT cycle running |
| `chlorine_production` | `[21]` | Raw value; `0` when not running |
| `electrode_polarity` | `[29]` bit `0x40` | set = RIGHT, clear = LEFT, *waiting* while `0x10` is clear |
| `salinity` | `[20]` | g/L, value / 10 |

---

## Where this lives in the decoder

The SALT profile is `custom_components/aseko_local/decoding/profiles/v7/salt.py`: the list of
features a SALT has, the readings that differ from the v7 defaults (the third-port routing,
winter mode from `byte[22]`), and the evidence for every entry. Each value's byte logic is one file in
`custom_components/aseko_local/decoding/features/`. The per-model table of what is confirmed is
generated into [`docs/support_matrix.md`](../support_matrix.md).

---

## Ground truth 2026-09-11 — Aseko Live app and unit display vs decoded frames

The maintainer's REDOX unit. Settings compared against the last captured
frame (2026-08-28); the settings had not changed in between. Live values are
from different days and are listed only to show the encoding, not the number.

| Field | Decoded (frame 2026-08-28) | App / display 2026-09-11 | Match |
|---|---|---|---|
| `redox_target` | 670 mV | Required values: Redox 670 mV | ✓ |
| `ph_target` | 7.2 | Required values: pH 7.2 | ✓ |
| `algaecide_dose_target` (byte[54], byte[37] bit 7 set) | 5 ml/m³/day | Algicide 5 ml/m³/day | ✓ |
| `water_temperature_target` | 25 °C | Water temp. `---` (Heating control OFF) | ⚠ byte[55] keeps the setpoint while the app hides it |
| `pool_volume` | 40 m³ | Pool volume 40 m³ | ✓ |
| `startup_delay` | 480 s | Delay time at startup 8 min | ✓ |
| `dosing_delay` | 240 s | Delay time after dose 4 min / display "4 min Delay time" | ✓ |
| `backwash_interval` | 15 | Backwash every 15 days | ✓ |
| `backwash_start_time` | 08:30 | Backwash starts at 08:30 | ✓ |
| `backwash_duration` | 100 s | Backwash takes 01:40 min | ✓ |
| `water_level_high_alarm` | 73 cm | 73 cm High level – Alarm | ✓ |
| `water_level_refill_stop` | 25 cm | 25 cm Filling OFF – Level OK | ✓ |
| `water_level_refill_start` | 10 cm | 10 cm Filling ON | ✓ |
| `water_level_low_alarm` | 5 cm | 5 cm Low level – Alarm | ✓ |
| `max_refill_time` (bytes 76–77) | 1140 s | Max filling time 19 min / display "19 min Max. time of filling" | ✓ |
| `ph_minus_concentration` (byte[112]) | 15 % | display "15 % Concentration pH−" | ✓ |
| `filtration_schedule` (byte[37] = 0xD3) | timer, period 1 | display: Timer filtration ON, Time period 1 ●, Time period 2 ✕, NONSTOP ○ | ✓ |
| `filtration_period_1_start` / `filtration_period_1_end` | 08:00 / 21:35 | Time period 1 8:00 → 21:35; app Filtration time 1 08:00 / 21:35 | ✓ |
| `filtration_period_2_start` / `filtration_period_2_end` | 18:10 / 23:55 | Time period 2 18:10 → 23:55 (disabled, still transmitted) | ✓ (Issue #133 behaviour) |
| `configuration` | REDOX | display "Choose the type of probe: Redox probe RX" | ✓ |
| `electrode_polarity` / `chlorine_production` | waiting / 0 | display "Power 0 g/h WAITING"; app "STOP WAITING" | ✓ |
| `salinity` | 4.0 kg/m³ (Aug) | 4.4 kg/m³ (Sep) | ✓ encoding; different day |
| `air_temperature` | None (open-circuit value) | display "air OFF", app "Air ---" | ✓ no probe → no value |
| `variable_speed_pump_enabled` (byte[22] bit 0x08) | False | display "VS Pump OFF" | ✓; the maintainer's other SALT has the bit set |
| `max_ph_doses` (byte[115]) | 20 | the unit's Safety Functions setting, 20 | ✓ — and changing it to 17 on 2026-09-12 moved the byte to 0x11 |
| `heating_running` | False | display "Heating control OFF", app "Heating ---" | consistent; the running state itself never captured |
| `water_level` | 31 cm (Aug) | 30 cm, "Filling OFF – Level OK" | ✓ encoding; the status text is derived from the thresholds |
| `refilling` (byte[29] bit 0x02) | set 2026-09-06 08:12 → 08:21 | the level fell to 10 cm (Filling ON), rose only while the bit was set and it cleared at 25 cm (Filling OFF) | ✓ from the Home Assistant history of that refill |

### What the remaining unknown bytes do (28 frames from one SALT, Aug–Sep 2026)

| Bytes | Behaviour | Reading |
|---|---|---|
| 64–65 | Tracks `ph` (bytes 14–15): equal in most frames, otherwise up to 0.70 pH away | the pH the regulation is working from — a lagging or smoothed copy, not new information |
| 66–67 | Tracks `water_temperature` (bytes 25–26): equal in most frames, otherwise up to 1.6 °C away | same, for the temperature |
| 39, 79, 119 | Last byte of each 40-byte segment, changes with every frame | checksum; not a plain sum of the segment payload |
| 32–36, 94, 100 | Always 0 | — |
| 72 | Always `0xFF` on SALT | `algaecide_dose_target` on the independent-port models; a SALT has no such port |
| 73, 108, 109–110, 111, 113, 116, 117, 118 | Constant on **both** SALT units (20, 10, 3000, 15, 1, 0xFF, 252, 1) and different on HOME/OXY | settings or model constants; changing one setting at a time per download would map them |
| 30, 31, 96, 97, 98, 114 | Vary frame to frame | the only bytes left that could carry anything live |
| 38 | Mostly 0; `0x10`, `0x20`, `0xA1`, `0x01` around heating and winter-mode changes | not decoded — see §Settings the frame does not carry |
| 78 | Heating allowed, winter active, VS pump type, filtration state | see §byte[78] |

---

### Visible on the unit or in the app, not decoded

| App / display item | Where it might live | What would settle it |
|---|---|---|
| Timeline error **"Low pH under 6,7 – increase pH"** | the HOME frame with pH 6.29 in `home_device_analysis.md` carries `byte[13]` = 0x28, i.e. bits 0x08 and 0x20 while the pH was under 6.7; the decoder currently calls 0x08 "rapid pH change" on the strength of error_codes.md alone | a download taken while the app shows this error; bytes 12–13 |
| Timeline error **"Water level too high"** | unknown; the level bytes are thresholds and the live level, not an alarm bit | a download during the alarm (the level above `water_level_high_alarm`); bytes 12–13 |
| Config toggle **Water flow meter** | unknown — the other toggles are mapped (§byte[37], §byte[22]) | toggle it with a marker after the next frame |
| Status **Pool flow OVERFLOW** (overflow vs. skimmer pool) | unknown | a marked test case switching the pool type |
| Consumption page: electrolyser efficiency / production kg/week, canister levels, pump lifetimes, water filled m³, heating kWh | cloud aggregates, not frame fields; production could be integrated locally from `chlorine_production` | — |
| The bytes that still vary: 30, 31, 96, 97, 98, 114 | measurements or counters — see the table above | correlate with the app's history |

---

## Open Questions

| Question | Status |
|---|---|
| pH− pump mask in byte[29]? | ⏳ Candidate `0x80` — consistent with HOME/OXY; awaiting frame |
| Electrode polarity? | ✅ `byte[29]` 0x40 set = right, clear = left — switched by hand both ways 2026-09-13 |
| byte[37] full field layout? | ✅ every bit mapped 2026-09-13 (§byte[37] – the whole byte); only `0x01` has no known meaning |
| byte[37] routing for Issue #84 firmware? | ⚠️ `0x13` = algicide but bit 7 NOT set — different firmware variant |
| byte[103] semantics? | ⏳ Always mirrors byte[101] on SALT — may be a duplicate or separate pump |
| `byte[115]` = max. number of pH doses? | ✅ Confirmed 2026-09-12 — the setting was changed 20 → 17 on the unit and byte[115] went 0x14 → 0x11, the only 17 in the frame.  Decoded as `max_ph_doses`. |
| Which `byte[13]` bit is "Low pH under 6,7"? | ⏳ 0x08 or 0x20 — the HOME frame with pH 6.29 had both set; 0x08 is currently read as rapid pH change |
| "Water level too high" alarm bit? | ⏳ Unknown — needs a download during the alarm |
| Config toggles? | ✅ heating control, winter mode, waterlevel, flow detection, VS pump, backwash schedule, heating condition (2026-09-13/14); ⏳ water flow meter and pool flow type |
| `byte[38]` bit 0x10 = heating parent to filtration? | ⏳ seen once in a session that changed several heating settings |
| Alarm bits on SALT (no flow, low salt, pH under 6.7)? | ⏳ needs a marked test case while the alarm is shown |
