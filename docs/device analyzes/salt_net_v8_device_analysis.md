# ASIN AQUA Salt NET (v8) — Device Analysis

[Documentation](../README.md) / [Device analyses](README.md)

> **Status:** the NET v8 layout plus the salt-only values below. Everything a
> salt unit sends on top of NET was read from frames an owner labelled with
> what the Aseko Live app showed at that moment (Issue #131); the shared part
> is the [NET v8](net_v8_device_analysis.md) layout, taken over unverified.
> **Profile:** [`profiles/v8/salt.py`](../../custom_components/aseko_local/decoding/profiles/v8/salt.py) · **Support:** [support matrix](../support_matrix.md)

## 1. Device

| Field | Value |
|---|---|
| Model | ASIN AQUA Salt NET |
| Firmware | 8.x text frames; header type 100 and 106 captured |
| Hardware | salt electrolysis cell (output in g/h, reversing polarity), pH probe and redox probe, pH− pump, one third pump port for algicide **or** flocculant, filtration relay |
| Identification | header type in the range 100–199: the product line picks the model, the rest of the number reads like the firmware version (1.00, 1.06) |
| Sources | Issue #131: labelled captures from one unit (header 100, 2026-07-09 … 07-19) and one frame with a display comparison from a second unit (header 106) |

The unit has **no chlorine canister**: the profile leaves out
`chlorine_pump_running` and `chlorine_flow_rate`, so a Salt NET no longer
shows a chlorine pump it does not have (the complaint in Issue #131).

## 2. Salt-only values

| Value | Position | Evidence |
|---|---|---|
| `salinity` | `ains[8]` / 10 (kg/m³) | confirmed: the display read **10.1** with `ains[8] = 101` in the same minute (header 106) |
| `chlorine_production` | `ains[9]` (g/h) | confirmed: **19** and **20** in captures their owner labelled 19 and 20 g/h, **0** with the electrolyser off |
| `electrolysis_running` | `outs[14]` ≠ 0 | confirmed on the labelled captures |
| `electrode_polarity` | `outs[14]`: 0 waiting, **2 right**, **3 left** | confirmed: the owner recorded the direction the app showed with each capture |
| `algaecide_pump_running` / `flocculant_pump_running` | `outs[11]`, the chemical from `fncs[6]` | observed: `fncs[6]` read **10** with algicide configured and **18** after the port was switched to flocculant on 2026-07-19; `outs[11] = 1` in the capture labelled "algicide pump running" |
| `algaecide_dose_target` | `areqs[4]` while `fncs[6] = 10` | observed: **5** with the unit set to 5 ml/m³/day, 0 after the switch |
| `flocculant_dose_target` | `areqs[3]` while `fncs[6] = 18` | observed: **10** with the unit set to flocculant 10 ml/h |
| `filtration_period_1_start` / `_end` | `reqs[5]` / `reqs[7]`, whole hours | observed: **8** and **20** on a unit its owner set to a timer from 08:00 to 20:00, **0** and **24** on one running nonstop |
| `filtration_schedule` | the same two hours: 0 to 24 nonstop, anything else the timer | derived from them; a v8 unit offers one period only |
| `alarm_no_flow_to_probes` | `ins[12]` bit `0x100` | derived: the flag the v8 decoder has always read; no capture shows it set |
| `alarm_max_disinfection_dose` | `ins[12]` bit `0x80` | observed: the value flipped 0 → 128 while the unit showed "Maximum disinfection dose exceeded" (Issue #151) |

The third pump port is one physical output. `fncs[6]` says which chemical it
is set up for, and the value for the other one is reported as not present, so
a unit dosing algicide gets no flocculant entities and the other way round —
the same rule the v7 SALT profile follows with its byte[37] routing bit.

## 3. Shared values checked on this model

The rest of the frame is the NET v8 layout. These entries were checked against
this model rather than taken over:

| Value | Position | Evidence |
|---|---|---|
| `ph` | `ains[0]` / 100 | 7.09 while the display read pH 7.1 in the same minute (firmware 106) |
| `redox` | `ains[6]` | 542 mV, matching the display |
| `water_temperature` | `ins[0]` / 10 | 29.5 °C, matching the display |
| `ph_target` / `redox_target` | `areqs[0]` / 10, `areqs[1]` × 10 | 7.1 and 720 mV, matching the setpoints on the display |
| `pool_volume` | `areqs[14]` | 55 m³ on the unit whose owner gave its pool as 55 m³ |
| `unit_clock`, `timestamp` | `ins[16]` hour, `ins[17]` minute | 18:25 and 08:01 in captures their owner timestamped 18:22:49 and 07:58:59 — the unit ran about two minutes ahead |
| `startup_delay`, `dosing_delay` | `areqs[17]`, `areqs[18]` | 5, the 5 min the unit is set to; a NET v8 sends 2 for its 2 min |

**No date is read.** `ins[13-15]` look like year, month and day but read
`24 7 9` on 15 July and `24 6 1` on 19 July, so `timestamp` takes its date
from Home Assistant and `unit_clock` is an hour and a minute only. The clock
offset entity therefore works to about a minute and within ±12 hours.

Still taken over unverified, because no capture separates them: the
filtration relay (`outs[2]`, which reads 2 here and 1 on a NET), water flow to
the probes (`ins[8]`, never seen 0) and the pH− pump (`outs[8]`).

## 4. Open questions

- **A changed timer.** The hours are read as start and stop (see above). A
  capture from a unit whose timer was changed to, say, 09:00-17:00 would
  confirm `reqs[5] = 9`, `reqs[7] = 17` directly.
- **The temperature setting is not captured.** The controller offers a third
  filtration setting next to nonstop and the timer, which runs the pump for
  water temperature / 2 + 2 hours a day (Issue #131; the manual, per
  hopkins-tk#162). No frame of a unit in it has been seen, so nothing decodes
  it: `filtration_schedule` knows only nonstop and the timer, and a unit in
  the temperature setting would most likely be reported as the timer, with
  whatever hours the unit computed for the day. A capture with the setting on,
  and a second one the next day at a different water temperature, would settle
  both where it is flagged and whether the hours move.
- **`fncs[2]`.** 1 on the first unit, 3 on the second, same hardware. It is not
  read, and the profile does not gate anything on it.
- **The shared NET values** (pH, redox, temperature, setpoints, pump bits) are
  taken over from the NET v8 profile and carry its evidence, not a Salt NET
  comparison.
- **No electrolyser setpoint** has been located: the unit sends the produced
  g/h, not the configured percentage.
