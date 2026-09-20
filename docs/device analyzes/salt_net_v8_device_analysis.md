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

## 3. Open questions

- **A changed timer.** The hours are read as start and stop (see above). A
  capture from a unit whose timer was changed to, say, 09:00-17:00 would
  confirm `reqs[5] = 9`, `reqs[7] = 17` directly.
- **`fncs[2]`.** 1 on the first unit, 3 on the second, same hardware. It is not
  read, and the profile does not gate anything on it.
- **The shared NET values** (pH, redox, temperature, setpoints, pump bits) are
  taken over from the NET v8 profile and carry its evidence, not a Salt NET
  comparison.
- **No electrolyser setpoint** has been located: the unit sends the produced
  g/h, not the configured percentage.
