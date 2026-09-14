# ASIN AQUA Home — Device Analysis

**Model**: ASIN AQUA HOME (CLF variant)
**Serial**: 110128063 (`0x06906bbf`)
**Device type byte**: `0x02` → `UNIT_TYPE_HOME_CLF`
**Source frame timestamp**: 2026-04-28 08:27:07
**Ground truth**: Aseko Live app screenshots (Status, Consumption, Config pages)

---

## One HOME, not two firmwares

Earlier versions of this document — and of the decoder — split HOME v7 into **firmware A** and
**firmware B** by bit `0x40` of `byte[37]`. That bit turned out to be a setting: toggling one setting
at a time on an ASIN AQUA Salt (2026-09-13) showed `0x40` is **Waterlevel (level meter) enabled**,
and the rest of `byte[37]` is one bit field of settings shared by HOME and SALT. Every HOME value once
read as a separate encoding decodes with the same bits:

| Bit | Mask | Meaning | HOME evidence |
|---|---|---|---|
| 0 | `0x01` | always set | every frame |
| 1 | `0x02` | Flow detection enabled | set in `0x43` / `0x53`; clear in Issue #135's `0x41` / `0x45` / `0x49` |
| 2 | `0x04` | settings menu open / manual override | `0x35` manual OFF (Issue #133); `0x47` / `0x57`, once called "transitional edit states" |
| 3 | `0x08` | Heating control enabled | Issue #135 |
| 4 | `0x10` | filtration period 1 enabled | Issue #133 |
| 5 | `0x20` | filtration period 2 enabled | Issue #133 |
| 6 | `0x40` | Waterlevel enabled | set on the units once called "firmware A", clear on serial 110169464 ("firmware B") and in the antifreeze frame `0x81` |
| 7 | `0x80` | antifreeze enabled | Issue #136 |

Bits `0x02` and `0x40` are confirmed on SALT and **derived** for HOME. These are **settings, not
hardware**: Waterlevel, Heating control or the VS pump can be switched on without the sensor or
device connected, and the app then simply shows nothing for it. That is why serial 110128063 sends
`0x43` (Waterlevel on) while the app showed `---` for the water level. A HOME owner toggling
*Waterlevel* and *Flow detection* once each, with a marked test case after each change, would confirm
the two bits on HOME (see Open Items).

The decoder has **one HOME profile**:
`custom_components/aseko_local/decoding/profiles/v7/home.py`.

---

## Raw Frame (120 bytes)

The Aseko protocol sends 3×40-byte segments in a single TCP payload.
Each segment header: `[0-3]` serial (big-endian), `[4]` device type, `[5]` segment marker (`0x01 / 0x03 / 0x02`), `[6-11]` timestamp.

```
Seg1 (bytes   0–39): 06 90 6b bf  02 01  1a 04 1c 08 1b 07
                     00 28 02 75 00 00 00 00 00 02 90 fe 70 01 7b 08 00 00 ff ff 00 00 00 00 00 43 0a 85

Seg2 (bytes  40–79): 06 90 6b bf  02 03  1a 04 1c 08 1b 07
                     46 03 0a 19 08 00 10 00 12 00 16 00 02 7c 01 7b 03 15 00 0c 00 28 01 e0 2a 30 a0 d8

Seg3 (bytes 80–119): 06 90 6b bf  02 02  1a 04 1c 08 1b 07
                     00 3c 00 3c 00 3c 00 3c 00 0a 0d 21 37 64 00 f0 14 02 58 0f 0f 0f 1e 14 ff bc 02 71
```

---

## Byte-by-Byte Analysis

### Segment 1 (bytes 0–39) — real-time sensor data

| Byte(s) | Hex      | Decimal | Field                    | Decoded value        | App value     | Status |
|---------|----------|---------|--------------------------|----------------------|---------------|--------|
| 0–3     | `06906bbf` | —     | Serial number (big-endian) | 110,128,063         | —             | ✓      |
| 4       | `02`     | 2       | Device type              | HOME (CLF variant)   | —             | ✓      |
| 5       | `01`     | 1       | Segment marker           | Segment 1            | —             | ✓      |
| 6–11    | `1a 04 1c 08 1b 07` | — | Timestamp           | 2026-04-28 08:27:07  | —             | ✓      |
| 12      | `00`     | 0       | **Dosing-warning bitmask** (`0x20`=disinfection, `0x40`=pH) | none           | —             | ✓ (Issue #134/#151) |
| 13      | `28`     | 40      | **Alarm bitmask** (`0x01`=disinfection, `0x02`=pH, `0x04`=no flow, `0x08`=rapid pH) | low nibble `0x08` set → rapid-pH flag (unconfirmed) | — | ✓ (Issue #151) |
| 14–15   | `0275`   | 629     | pH (÷100)                | **6.29**             | 6.56†         | ✓†     |
| 16–17   | `0000`   | 0       | Cl free (÷100)           | **0.00 mg/l**        | 0.00 mg/l     | ✓      |
| 18–19   | `0000`   | 0       | Unused (no REDOX probe)  | —                    | —             | —      |
| 20–21   | `0002`   | 2       | Cl free mV (big-endian)  | **2 mV**             | —             | ✓      |
| 22      | `90`     | 144     | Settings flags (see ¶)   | backwash schedule on (`0x10`) | every 3 days | ¶ |
| 23–24   | `fe70`   | —       | Air temperature          | open-circuit value → not present | — | ✓ no probe |
| 25–26   | `017b`   | 379     | Water temp (÷10)         | **37.9°C**           | 38.2°C†       | ✓†     |
| 27      | `08`     | 8       | **Water level (cm)**     | **8 cm**             | (level meter disabled on this device) | ✓     |
| 28      | `00`     | 0       | Water flow to probes     | **False** (≠ 0xAA)   | NO            | ✓      |
| 29      | `00`     | 0       | Actuator bits            | all pumps stopped    | STOP          | ✓      |
| 30–31   | `ffff`   | —       | UNSPECIFIED / padding    | —                    | —             | —      |
| 32–36   | `00…00`  | 0       | Unknown                  | —                    | —             | ?      |
| 37      | `43`     | 67      | **Settings flags**       | nonstop 24 h, flow detection, waterlevel (see §) | NONSTOP 24H | ✓ |
| 38      | `0a`     | 10      | Unknown                  | —                    | —             | ?      |
| 39      | `85`     | 133     | Unknown (checksum?)      | —                    | —             | ?      |

† pH 6.29 vs 6.56 and water temp 37.9 vs 38.2 are explained by different timestamps (frame: 08:27:07, screenshot: later that day). Not a decoding bug.

§ **byte[37] = `0x43`** = `0x40` waterlevel + `0x02` flow detection + `0x01`; no period bit, so
*FILTRATION NONSTOP 24H*. HOME devices have **independent pump ports** for flocculant and algicide
(same layout as OXY Pure), so bit 7 is antifreeze here, not SALT's shared-port routing. The whole
byte is described in *One HOME, not two firmwares* above.

¶ **byte[22]** is a settings byte. Bit `0x08` is the **VS pump setting** (Issue #137: `0x83` off,
`0x8b` on) and bit `0x10` the backwash schedule (set here with backwash every 3 days) — both
confirmed on SALT by toggling them. On SALT bits `0x01` / `0x02` / `0x20` are the heating condition
(time window / outside temperature / below), never both `0x01` and `0x02`; the HOME VSP frames carry
`0x83` with both set, so the heating condition is **not** decoded on HOME until a HOME frame explains
them. Bit `0x80` is unknown.

---

### Segment 2 (bytes 40–79) — setpoints and schedule

| Byte(s) | Hex      | Decimal | Field                         | Decoded value  | App value         | Status |
|---------|----------|---------|-------------------------------|----------------|-------------------|--------|
| 40–43   | `06906bbf` | —     | Serial (repeated)             | 110,128,063    | —                 | ✓      |
| 44      | `02`     | 2       | Device type (repeated)        | HOME           | —                 | ✓      |
| 45      | `03`     | 3       | Segment marker                | Segment 2      | —                 | ✓      |
| 46–51   | `1a 04 1c 08 1b 07` | — | Timestamp (repeated)       | 2026-04-28 08:27:07 | —            | ✓      |
| 52      | `46`     | 70      | ph_target (÷10)             | **7.0**        | 7.0               | ✓      |
| 53      | `03`     | 3       | free_chlorine_target (÷10)        | **0.3 mg/l**   | 0.3               | ✓      |
| 54      | `0a`     | 10      | flocculant_dose_target                 | **10 ml/h**    | 10 ml/h           | ✓      |
| 55      | `19`     | 25      | water_temperature_target    | 25°C           | — (disabled)      | ⚠ Open Item 3 |
| 56–57   | `08 00`  | —       | start1                        | 08:00          | last-configured   | ✓     |
| 58–59   | `10 00`  | —       | stop1                         | 16:00          | last-configured   | ✓     |
| 60–61   | `12 00`  | —       | start2                        | 18:00          | last-configured   | ✓     |
| 62–63   | `16 00`  | —       | stop2                         | 22:00          | last-configured   | ✓     |
| 64–65   | `027c`   | 636     | Unknown                       | —              | —                 | ?      |
| 66–67   | `017b`   | 379     | Unknown (= water temp raw)    | —              | —                 | ?      |
| 68      | `03`     | 3       | backwash_interval         | **3 days**     | every 3 days      | ✓      |
| 69–70   | `15 00`  | —       | backwash_start_time                 | **21:00**      | starts at 21:00   | ✓      |
| 71      | `0c`     | 12      | backwash_duration (×10 s)     | **120 s = 2 min** | takes 02:00 min | ✓    |
| 72      | `00`     | 0       | algaecide_dose_target             | **0 ml/m³/day** | 0 ml/m³/day     | ✓      |
| 73      | `28`     | 40      | Unknown                       | —              | —                 | ?      |
| 74–75   | `01e0`   | 480     | startup_delay (s)       | **480 s = 8 min** | 8 min          | ✓      |
| 76–77   | `2a30`   | 10800   | max_refill_time (s)          | **10800 s = 180 min** | —          | ✓ (bytes verified on SALT vs Aseko Live, v1.9) |
| 78      | `a0`     | 160     | Unknown                       | —              | —                 | ?      |
| 79      | `d8`     | 216     | Unknown                       | —              | —                 | ?      |

> **Schedule vs. mode flag**: bytes 56-63 always carry the last-configured
> schedule (the unit does not clear them when switching to NONSTOP 24h). The
> actual mode is reported separately in `byte[37]`. See the *byte[37]
> — Filtration mode flag* section under "Device Specifications" below for the
> two encodings.

---

### Segment 3 (bytes 80–119) — pool parameters and flowrates

| Byte(s) | Hex      | Decimal | Field                        | Decoded value  | App value         | Status |
|---------|----------|---------|------------------------------|----------------|-------------------|--------|
| 80–83   | `06906bbf` | —     | Serial (repeated)            | 110,128,063    | —                 | ✓      |
| 84      | `02`     | 2       | Device type (repeated)       | HOME           | —                 | ✓      |
| 85      | `02`     | 2       | Segment marker               | Segment 3      | —                 | ✓      |
| 86–91   | `1a 04 1c 08 1b 07` | — | Timestamp (repeated)      | 2026-04-28 08:27:07 | —            | ✓      |
| 92–93   | `003c`   | 60      | pool_volume (big-endian)     | **60 m³**      | 60 m³             | ✓      |
| 94–95   | `003c`   | 60      | Unknown (read as max_refill_time before v1.9; that value is bytes 76–77) | — | —     | ?      |
| 96      | `00`     | 0       | Unknown                      | —              | —                 | ?      |
| 97      | `3c`     | 60      | ph_plus_flow_rate? (unconf.)  | —              | —                 | ?      |
| 98      | `00`     | 0       | Unknown                      | —              | —                 | ?      |
| 99      | `3c`     | 60      | chlorine_flow_rate               | **60 ml/min**  | Chlor Pure listed | ✓      |
| 100     | `00`     | 0       | Unknown                      | —              | —                 | ?      |
| 101     | `0a`     | 10      | **flocculant_flow_rate**            | **10 ml/min**  | Floc+c listed     | ✓ (fixed) |
| 102     | `0d`     | 13      | **water_level_low_alarm (cm)** | **13 cm**    | Low alarm         | ✓ (Issue #110) |
| 103     | `21`     | 33      | **algaecide_flow_rate**        | **33 ml/min**  | Algicide listed   | ✓ (fixed) |
| 104     | `37`     | 55      | **water_level_refill_stop (cm)** | **55 cm**  | Filling OFF       | ✓ (Issue #110) |
| 105     | `64`     | 100     | **water_level_high_alarm (cm)** | **100 cm**  | High alarm        | ✓ (Issue #110) |
| 106–107 | `00f0`   | 240     | dosing_delay (s)         | **240 s = 4 min** | 4 min          | ✓      |
| 108     | `14`     | 20      | Unknown                      | —              | —                 | ?      |
| 109–110 | `0258`   | 600     | Unknown                      | —              | —                 | ?      |
| 111     | `0f`     | 15      | Unknown                      | —              | —                 | ?      |
| 112     | `0f`     | 15      | **ph_minus_concentration**   | **5%**         | **5%**           | ✓ (Issue #139) |
| 113     | `0f`     | 15      | Unknown                      | —              | —                 | ?      |
| 114     | `1e`     | 30      | Unknown                      | —              | —                 | ?      |
| 115     | `14`     | 20      | **max_ph_doses** (safety: max. number of pH doses) | **20** | —      | ✓ position confirmed on SALT 2026-09-12; HOME value not compared |
| 116     | `ff`     | —       | UNSPECIFIED / padding        | —              | —                 | —      |
| 117     | `bc`     | 188     | Unknown                      | —              | —                 | ?      |
| 118–119 | `0271`   | 625     | Unknown (checksum?)          | —              | —                 | ?      |

Note on **bytes 94–95**: `max_refill_time` reads bytes[94:96] as a big-endian 16-bit value = `0x003c` = 60. `ph_minus_flow_rate` independently reads byte[95] = `0x3c` = 60. They overlap but coincidentally produce the same result because the high byte (94) is 0x00. If byte[94] ever becomes non-zero the max_refill_time would be inflated; however for HOME this is expected to fit in one byte (max ~255 min).

---

## Dosing warnings & alarms (bytes 12 / 13)

HOME devices report dosing safety faults in two adjacent bytes. The decoder reads
them on every model with alarms (`decoding/features/alarm_*.py`):

| Binary sensor | byte[12] bit | byte[13] bit |
|---|---|---|
| Too many doses of disinfection (`alarm_max_disinfection_dose`) | `0x20` | `0x01` |
| Too many doses of pH (`alarm_ph_dosing_ineffective`) | `0x40` | `0x02` |
| No flow to probes (`alarm_no_flow_to_probes`) | — | `0x04` |
| Rapid pH change (`alarm_rapid_ph_change`) | — | `0x08` (unconfirmed) |

Confirmed by @dtpugh's diagnostics on HOME serial 110175608 (byte[4] = `0x03`):

* **Issue #134** (2026-07-05), before/after clearing on the controller: both
  warnings active → byte[12] = `0x60`; pH only → `0x40`; cleared → `0x00`.
  byte[13] stayed `0x00`.
* **Issue #151** (2026-08-06/08): chlorine/disinfection "Maximum disinfection
  dose exceeded" → byte[13] = `0x01` (byte[12] = `0x00`); pH fault → byte[12] =
  `0x40`; cleared → both `0x00`.

The disinfection fault was observed in byte[12] `0x20` (July) **and** in byte[13]
`0x01` (August) — likely a firmware change on the Home. The decoder ORs both
paths so either encoding is detected. The byte[13] `0x02` = pH mapping is
**inferred** (symmetric to `0x01`; @dtpugh expected `0x02` for a pH fault) and
still lacks a direct frame capture. The same disinfection fault maps to `ins[12]`
bit `0x80` on v8 frames (Issue #151, `decode_v8` in `features/alarm_max_disinfection_dose.py`), so both protocols
share the `alarm_max_disinfection_dose` sensor.

---

## Decoded Values vs Ground Truth Summary

| Field                     | Decoded          | Aseko Live        | Match |
|---------------------------|------------------|-------------------|-------|
| pH                        | 6.29             | 6.56              | ✓ (Δt)|
| Cl free                   | 0.00 mg/l        | 0.00 mg/l         | ✓     |
| Water temperature         | 37.9°C           | 38.2°C            | ✓ (Δt)|
| Water flow to probes      | False            | NO                | ✓     |
| Filtration pump running   | False            | STOP              | ✓     |
| filtration_schedule       | NONSTOP_24H      | NONSTOP 24H       | ✓ (Issue #110) |
| service_menu_open         | False            | (nobody at the unit) | ✓ |
| water_level               | 8 cm             | --- (level meter disabled) | ✓ (frame value) |
| water_level_low_alarm     | 13 cm            | (config)          | ✓ (Issue #110) |
| water_level_refill_start    | 33 cm            | (config)          | ✓ (Issue #110) |
| water_level_refill_stop   | 55 cm            | (config)          | ✓ (Issue #110) |
| water_level_high_alarm    | 100 cm           | (config)          | ✓ (Issue #110) |
| refilling      | False            | --- (valve not active) | ✓ (Issue #100) |
| ph_target               | 7.0              | 7.0               | ✓     |
| free_chlorine_target          | 0.3 mg/l         | 0.3               | ✓     |
| flocculant_dose_target             | 10 ml/h          | 10 ml/h           | ✓ (fixed) |
| algaecide_dose_target         | 0 ml/m³/day      | 0 ml/m³/day       | ✓ (fixed) |
| water_temperature_target | 25°C            | --- (disabled)    | ⚠ Open Item 3 |
| Filtration times          | 08:00–16:00 / 18:00–22:00 (last-configured) | NONSTOP 24H | ✓ (schedule from `byte[37]`, time bytes always present) |
| backwash_interval     | 3                | every 3 days      | ✓     |
| backwash_start_time             | 21:00            | starts at 21:00   | ✓     |
| backwash_duration         | 120 s            | 02:00 min         | ✓     |
| pool_volume               | 60 m³            | 60 m³             | ✓     |
| startup_delay       | 480 s (8 min)    | 8 min             | ✓     |
| dosing_delay          | 240 s (4 min)    | 4 min             | ✓     |
| ph_minus_flow_rate         | 60               | pH- listed        | ✓     |
| chlorine_flow_rate            | 60               | Chlor Pure listed | ✓     |
| flocculant_flow_rate             | 10               | Floc+c listed     | ✓     |
| algaecide_flow_rate         | 33               | Algicide listed   | ✓ (fixed) |
| heating_control_enabled   | True / False     | — (app setting)   | ✓ (Issue #135, serial 110175608 REDOX HOME) |
| freeze_protection_enabled        | True / False     | — (app setting)   | ✓ (Issue #136, serial 110175608 REDOX HOME) |
| variable_speed_pump_enabled          | True / False     | — (app setting)   | ✓ (Issue #137, serial 110175608 REDOX HOME) |
| ph_minus_concentration    | 5%               | 5%                | ✓ (Issue #139, serial 110175608 REDOX HOME) |

---

## Device Specifications

### Pump ports

HOME has **4 independent pump ports** (same layout as OXY Pure), unlike SALT
which has a shared third-pump port. There is no SALT-style algicide/flocculant
routing via `byte[37]` bit 7.

| Port  | Pump                | `flowrate_*` byte | `flowrate_*` value | `byte[29]` bit (uncertain) | `byte[29]` mask |
|-------|---------------------|-------------------|--------------------|-----------------------------|-----------------|
| 1     | pH− (Ph minus)      | `byte[95]`        | `ph_minus_flow_rate`  | bit 7                       | `0x80`          |
| 2     | Chlorine / OXY Pure | `byte[99]`        | `chlorine_flow_rate`     | bit 6                       | `0x40`          |
| 3     | Flocculant          | `byte[101]`       | `flocculant_flow_rate`      | bit 5                       | `0x20`          |
| 4     | Algicide            | `byte[103]`       | `algaecide_flow_rate`  | bit 4 (PROFI/SALT) / bit 5 (HOME, shared) | `0x20` |

> **Note on cl/oxy routing**: the chlorine pump port can be configured as
> Chlorine OR OXY Pure (same physical port, same bit in `byte[29]`). The
> routing byte is not yet confirmed from frames — see Open Item 7.

### Setpoints

| Field                   | Byte(s)   | Unit             | Notes |
|-------------------------|-----------|------------------|-------|
| `ph_target`           | `byte[52]`| (raw ÷ 10)        |       |
| `free_chlorine_target`      | `byte[53]`| mg/L (raw ÷ 10)   | HOME CLF variant only |
| `redox_target`        | `byte[53]`| mV (raw × 10)     | HOME REDOX variant only |
| `flocculant_dose_target`         | `byte[54]`| ml/h              | Same byte position as SALT algicide; gated by `byte[37] != 0xFF` |
| `algaecide_dose_target`     | `byte[72]`| ml/m³/day         | HOME-only, same byte position as OXY Pure |
| `water_temperature_target` | `byte[55]` | °C            | Antifreeze setpoint while antifreeze is on — see Open Item 3 |
| `ph_minus_concentration`     | `byte[112]`| %             | pH⁻ acid concentration (Issue #139); the same byte on SALT |

### Schedule (bytes 56-63)

| Field   | Byte(s)   | Decoded      | Notes |
|---------|-----------|--------------|-------|
| `filtration_period_1_start` | `byte[56:58]` | HH:MM | |
| `filtration_period_1_end`   | `byte[58:60]` | HH:MM | |
| `filtration_period_2_start` | `byte[60:62]` | HH:MM | Always transmitted — see Issue #133 |
| `filtration_period_2_end`   | `byte[62:64]` | HH:MM | Always transmitted — see Issue #133 |

### `byte[37]` — settings flags

The bits are listed in *One HOME, not two firmwares* at the top. Every captured HOME value, read
with them:

| `byte[37]` | Source | Schedule | Menu | Heating control | Antifreeze | Flow detection | Waterlevel |
|---|---|---|---|---|---|---|---|
| `0x43` | Issue #110 | nonstop 24 h | — | — | — | ✓ | ✓ |
| `0x53` | Issue #110 | period 1 | — | — | — | ✓ | ✓ |
| `0x47` / `0x57` | Issue #110 | nonstop / period 1 | ✓ | — | — | ✓ | ✓ |
| `0x01` | Issue #133 | nonstop 24 h | — | — | — | — | — |
| `0x11` | Issue #133 | period 1 | — | — | — | — | — |
| `0x31` | Issue #133 | periods 1 and 2 | — | — | — | — | — |
| `0x35` | Issue #133 | periods 1 and 2 | ✓ (manual OFF) | — | — | — | — |
| `0x41` | Issue #135 | nonstop 24 h | — | — | — | — | ✓ |
| `0x45` | Issue #135 | nonstop 24 h | ✓ | — | — | — | ✓ |
| `0x49` | Issue #135 | nonstop 24 h | — | ✓ | — | — | ✓ |
| `0x81` | Issue #136 | nonstop 24 h | — | — | ✓ | — | — |

Two consequences of reading it this way, both differences from the old firmware-A decoding:

* `0x53` is **period 1**, not "period 1 and 2": bit `0x20` is clear.
* `0x47` / `0x57` decode to a schedule (nonstop / period 1) with the menu open, instead of no schedule.

When antifreeze is on, `byte[55]` drops from the heating setpoint (e.g. 27 °C) to the antifreeze
setpoint (e.g. 4 °C, 5 °C or 9 °C, whatever the user sets). On SALT the corresponding *winter mode*
lives in `byte[22]` `0x04`, because `0x80` is the algicide routing there.

**Note on `0x43`**: treat this as "consistent with NONSTOP 24H" rather
than "confirmed NONSTOP 24H active". A frame captured in May 2026 from
mannekung's device (after switching to NONSTOP 24H) still showed `0x53` (timer)
with the Aseko app in "Suche" (search) mode — see [Issue #110 frame
discussion](https://github.com/hopkins-tk/home-assistant-aseko-local/issues/110).

**Note on `0x35` (manual OFF)**: when this value appears, `byte[29]`
bit 3 (`filtration_running`) is still set in the frame — the firmware does
not clear the schedule-driven bit on manual override. The decoder compensates
by short-circuiting `filtration_running` to `False` whenever
`service_menu_open is True`.

This override stays **HOME-only**, and SALT captures are now the reason why
rather than just a lack of evidence: there the same bit marks the settings
menu being open, which says a person is at the unit and nothing about what
they did — they may equally have switched the pump *on*.  Forcing it off
would invent a state the unit never reported.  See
`salt_device_analysis.md` §byte[37] – filtration mode and schedule.

Whether HOME's bit is literally the same menu flag is **unverified**: the
four Issue #133 frames were downloaded one per mode, so a HOME unit going
quiet the way SALT does would not have shown up in them.  If it does, the
override here is reading a menu session rather than a standing override.

**Note on Period 2 schedule bytes (Issue #133)**: All Aseko devices with a
filtration output (SALT, HOME, OXY, PROFI) keep sending the last-configured
`start2`/`stop2` times in bytes 60-63 even after the user disables Period 2
in the controller UI. The controller never clears these bytes — they are
treated as the device's "last-known schedule" and the active/inactive
state is carried separately in `byte[37]` bit 5 (`0x20`) on HOME, SALT and OXY.
Pre-fix, the decoder used `byte[37]` bit 0x20 to gate `start2`/`stop2` on
None for any device where the enable flag was clear, which caused
already-registered entities to flip to "unknown" when the user toggled
the controller back from "P1 & P2" to "P1 only" (the entity registry
protects the entity, but the value is read as `None`).  Post-fix, bytes
60-63 are read unconditionally on every model with a filtration output (so
`start2`/`stop2` stay populated and the entity shows the last-configured
time); the `filtration_schedule` sensor separately reports `TIMER_PERIOD_1`
to tell the user that Period 2 is inactive.  This behaviour was
verified against the four diagnostic files from
[Issue #133](../temp/Issue-133.md) (serial 110169464, ASIN AQUA Home): bytes 60-63 stay populated in all four modes (24h nonstop,
P1 only, P1 & P2, OFF manual).  The decoder applies the same logic to
SALT/OXY/PROFI for two reasons:

1.  SALT and OXY share the same protocol layout for bytes 60-63, and
    `byte[37]` bit 0x20 is the documented enable flag on those devices.
    There is no protocol-level reason to believe they clear the bytes
    when Period 2 is disabled.
2.  PROFI has the same byte layout but no live frame has been captured
    that toggles Period 2 on/off; the same fix prevents a potential
    regression if a user reports the same "unknown entity" symptom on
    PROFI later.

NET is excluded because it has no filtration output at all: its
profile does not list the filtration features.

### `byte[29]` — Actuator bitmask (HOME)

Bit positions in `byte[29]` for HOME pump states, as read by the HOME profile. The per-pump bits for
HOME-specific pumps (algicide, flocculant) are **not yet confirmed** by live capture (see Open Item 7).

| Bit  | Mask  | Field                       | Confidence |
|------|-------|-----------------------------|------------|
| 0    | `0x01`| backwash valve relay        | ✓ confirmed (HOME/SALT/OXY all use this bit) |
| 1    | `0x02`| water-filling active        | ✓ confirmed (Issue #100; on SALT 2026-09-06 against the refill thresholds) |
| 2    | `0x04`| heating active              | ⚠ unconfirmed — see Open Item 9                |
| 3    | `0x08`| filtration pump running     | ✓ confirmed (every model with filtration)     |
| 4    | `0x10`| algicide pump running       | assumed as on OXY (same four ports); read once the algicide flow rate is located |
| 5    | `0x20`| flocculant pump running     | assumed as on OXY (confirmed there) |
| 6    | `0x40`| cl pump running             | see Open Item 7        |
| 7    | `0x80`| pH− pump running            | see Open Item 7        |

### `byte[29]` vs `service_menu_open` (manual OFF)

Cross-frame analysis of @dtpugh's four Issue #133 frames (24h nonstop, P1 only,
P1 & P2, OFF manual) shows that `byte[29]` bit 3 stays set in **all four**
frames — including the OFF frame. The override state lives in `byte[37]` bit 2
(value `0x35`), not in `byte[29]`. The HOME profile reads `filtration_running` with
`decode_v7_menu_override` (`decoding/features/filtration_running.py`), which reports the pump off
while that bit is set.

Bit 2 is decoded into `service_menu_open` (a plain bool) and the schedule bits
into `filtration_schedule`.  They are unrelated facts sharing a byte: one says
somebody is at the unit, the other what it runs when nobody is.

### `byte[22]` / `byte[78]` — Variable-speed filtration pump (Issue #137)

Some HOME REDOX devices (serial 110175608) support a variable-speed filtration pump. The brand is
picked on the unit and in the Aseko app (Speck, Pentair, Hayward, Dab E.SWIM, Uwe EO PM).

**byte[22] bit 3 (0x08)** is the **VS pump setting**, not the pump running: `0x83` off, `0x8b` on
(any brand). Confirmed on SALT, where switching *VS Pump* on the unit sets and clears it. Decoded as
`variable_speed_pump_enabled` on HOME, SALT and OXY.

**byte[78] bits 0x0C** are the **pump type**. The unit stores a protocol group, not a brand, so two
brands share a value:

| `byte[78]` on HOME | bits `0x0C` | Pump type (`variable_speed_pump_type`) |
|---|---|---|
| `0x22` | `0x00` | Speck / Uwe EO PM (also shown with the VS pump off: the type is kept) |
| `0x26` | `0x04` | Pentair / Dab E.SWIM |
| `0x2a` | `0x08` | Hayward |

The same groups were confirmed on SALT by selecting every brand in turn. The other bits of `byte[78]`
on SALT: `0x80` heating allowed now, `0x40` winter mode active, `0x02` / `0x01` filtration running /
standing. The HOME values all have `0x02` set (filtration running at capture) and `0x20`, whose
meaning is unknown.

---

## Open Items

| # | Description |
|---|-------------|
| 3 | `water_temperature_target` vs app "---" — partially resolved by Issue #135: `byte[55]` is confirmed as the heating setpoint on serial 110175608 (REDOX HOME, heating ON frame). A frame from a device where the app actively shows a target temperature (not "---") would further validate this. |
| 7 | `byte[29]` per-pump bits for HOME (algicide, flocculant, cl, pH−) are unconfirmed. The HOME profile reads them with the OXY/NET bit positions, which are placeholders here. Capturing frames with a single HOME pump running (e.g. algicide only) would pin down the per-pump bit. Until then, `algaecide_pump_running` and `flocculant_pump_running` may report incorrectly on HOME. |
| 8 | ~~`max_refill_time` overlap with `ph_minus_flow_rate`~~ — resolved: `max_refill_time` is bytes 76–77 in seconds (verified on SALT against Aseko Live, v1.9); bytes 94–95 are back to unknown. |
| 12 | `byte[103]` was read both as `algaecide_flow_rate` (33 ml/min) and as `water_level_refill_start` (33 cm) on serial 110128063. Decided for the threshold: bytes 102-105 are the level thresholds on SALT (confirmed against the unit) and 13 / 33 / 55 / 100 cm are in order here; OXY sends its algicide flow rate on byte[103] only because it has no level sensor. HOME's algicide flow rate is **not located** (entity unknown), so neither the algicide pump state nor its consumption is computed until it is found. Before, bit `0x20` counted algicide and flocculant for one running pump; the pump bits now follow OXY (algicide `0x10`, flocculant `0x20`). |
| 9 | `heating_running` binary sensor (`byte[29]` bit `0x04`) — needs a frame captured while the heat pump / electric heater is actually running. The `heating_control_enabled` field (byte[37] bit 3) is the **master enable**, separate from the actual heating output state in byte[29] bit 2. A frame with `byte[29]` bit 2 set would confirm this as the running-state indicator. |
| 10 | Bytes 31, 38, 65 in the `0x35` manual OFF frame all rise by ~1 (0x00→0x02, 0x02→0x03, 0xa3→0xa4) — possible additional "manual override active" sub-flags, not used by the decoder today. Single observation, no meaning assigned. |
| 11 | ~~`byte[78]` brand ID or pump parameter~~ — resolved: bits `0x0C` are the pump type group (Speck/Uwe, Pentair/Dab, Hayward), confirmed on SALT. `0x20` is still unknown. |
| 13 | `byte[37]` bits `0x40` (Waterlevel) and `0x02` (Flow detection) are confirmed on SALT only; they are settings, so a unit without a level sensor can still have `0x40` set (serial 110128063). A HOME owner toggling each setting once, with a marked test case after each change, would confirm or refute them on HOME. |
| 14 | `byte[22]` on the HOME VSP unit is `0x83`: bits `0x01` and `0x02` both set, which never happens on SALT (heating by time window vs by outside temperature), and `0x80` unknown. Heating condition is not decoded on HOME until a HOME frame explains these. |

---

## Test Coverage

Tests for the HOME decoder live in `tests/test_decode_v7.py` and `tests/test_decoding_profiles.py`:

| Test | Covers |
|------|--------|
| `test_decode_home` | End-to-end HOME REDOX frame decoding, including schedule + max_refill_time |
| `test_decode_home_clf_real_frame` | Issue #110: real HOME CLF frame |
| `test_home_issue_110_frame` | Issue #110 frame: `byte[37]` = `0x53` → period 1, waterlevel enabled |
| `test_decode_home_independent_flowrates` | Issue #115: HOME reads `byte[101]` and `byte[103]` independently of `byte[37]` |
| `test_decode_home_flowrates_unspecified` | 0xFF on flowrate bytes → `None` (pump not installed) |
| `test_decode_home_algicide_pump_running` | Issue #115: `algaecide_pump_running` is decoded |
| `test_decode_home_floc_pump_running_independent` | HOME reports `flocculant_pump_running` when only the floc pump is installed |
| `test_filtration_schedule_new_encoding_24h` / `_p1` / `_p1_and_p2` | Issue #133: `0x01` / `0x11` / `0x31` → schedule |
| `test_service_menu_new_encoding_p1_and_p2` | Issue #133: `0x35` → `service_menu_open` True |
| `test_filtration_schedule_old_encoding_24h` / `_timer` | Issue #110: `0x43` → nonstop, `0x53` → period 1 with waterlevel enabled |
| `test_filtration_schedule_with_the_menu_open_is_read_from_the_bits` | `0x47` / `0x57` → nonstop / period 1 with the menu open |
| `test_filtration_pump_running_off_when_manual_override` | Issue #133: `0x35` forces `filtration_running=False` |
| `test_filtration_pump_running_on_when_not_override` | `byte[29]&0x08` still drives the entity while bit 0x04 is clear |
| `test_filtration_pump_running_not_overridden_on_salt` | The override is HOME-only |
| `test_decode_filtration_period2_real_dtpugh_frames` | Issue #133: end-to-end against @dtpugh's four diagnostic files |
| `test_every_home_frame_uses_the_one_home_profile` | Every `byte[37]` value decodes with the one HOME profile |
| `test_home_byte37_is_one_bit_field` | Waterlevel, flow detection, menu and schedule read from one byte |
| `test_home_menu_override_forces_the_pump_off` | Profile-level check of the manual OFF override |

---

## Cross-References

- Related decoder files: `custom_components/aseko_local/decoding/profiles/v7/home.py` (profile) and `custom_components/aseko_local/decoding/features/` (one file per value)
- Support matrix (what is confirmed per model): `docs/support_matrix.md`
- OXY analysis (reference for shared byte layout): `docs/device analyzes/oxy_device_analysis.md`
- NET v8 analysis: `docs/device analyzes/net_v8_device_analysis.md`
- Issue #110: `byte[37]` = `0x43` nonstop 24 h — original finding, frames in this file
- Issue #115: HOME `algaecide_pump_running` missing — fixed by independent-pump-port branch
- Issue #133: `byte[37]` period bits and the manual OFF bit. Period 2 schedule bytes (60-63) are read unconditionally to avoid "unknown" entities when the user toggles the controller — see the *Note on Period 2 schedule bytes (Issue #133)* above.
- Issue #135: `byte[37]` bit 3 (`0x08`) = heating control master enable
  (serial 110175608, REDOX HOME). Confirms `byte[55]` as target water temp setpoint.
  Working notes: [docs/temp/Issue-135.md](../temp/Issue-135.md).
- Issue #136: `byte[37]` bit 7 (`0x80`) = antifreeze master enable
  (same device). `byte[55]` shows the antifreeze setpoint (e.g. 4°C, 5°C, 9°C)
  when enabled.
- Issue #137: `byte[22]` bit 3 (`0x08`) = variable-speed pump setting; `byte[78]` bits `0x0C` =
  pump type group (Speck/Uwe, Pentair/Dab, Hayward).
- Issue #139: `byte[112]` = pH⁻ acid concentration (%) on HOME (serial 110175608).
  Confirmed 5% → 10% → 5% across three diagnostics.
- Working notes: `docs/temp/Issue-133.md`
