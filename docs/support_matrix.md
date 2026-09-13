# Support matrix

What each decoding profile reads, and how sure we are.  Generated from `custom_components/aseko_local/decoding/profiles/` by `scripts/generate_support_matrix.py`; do not edit by hand.

A **profile** is one (protocol, model, firmware) combination.  A **feature** is one field on `AsekoDevice`, i.e. one value the integration can read.

| Mark | Meaning |
|---|---|
| ✅ | read on this model, checked against the unit display or the Aseko Live app |
| 👁 | seen repeatedly in captures from a real unit with consistent, plausible values, but not compared with the unit display or the app — **a glance at the unit would settle it** |
| ❓ | read on this model, but never seen with a real value in any capture — **a diagnostics dump would settle it** |
| — | this model does not have the value, so no entity is created for it |
| 🔍 | this model has the value (its menu or manual shows it), but where the frame carries it is not known yet: the entity exists and reads unknown — **a diagnostics dump before and after changing it on the unit would settle it** |
| `decode_…` | the profile uses this reading instead of the protocol default |

Two further profiles exist that no unit is meant to decode with and that the tables leave out: **v7 HOME firmware not yet known** and **v7 unknown unit type**.  The first reads what both HOME firmware revisions share while a frame with `byte[37]` unset cannot tell them apart; the second reads everything that has a generic v7 reading so an unmapped unit shows as much as possible in diagnostics, where it is reported as unrecognised.

## v7

| field | HOME firmware A | HOME firmware B | SALT | OXY | NET | PROFI |
|---|---|---|---|---|---|---|
| `air_temperature` | ❓ | ❓ | ✅ | ❓ | — | — |
| `alarm_max_disinfection_dose` | ✅ | ✅ | ✅ | ❓ | ❓ | ❓ |
| `alarm_no_flow_to_probes` | ✅ | ✅ | ✅ | ❓ | ✅ | ❓ |
| `alarm_ph_dosing_ineffective` | ✅ | ✅ | ✅ | ❓ | ❓ | ❓ |
| `alarm_rapid_ph_change` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| `algaecide_dose_target` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | — | — |
| `algaecide_flow_rate` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | — | — |
| `algaecide_pump_running` | ❓ | ❓ | ✅ | ✅ `decode_v7_oxy` | — | — |
| `backwash_duration` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `backwash_interval` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `backwash_running` | ❓ | ❓ | ✅ | ❓ | — | ❓ |
| `backwash_start_time` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `chlorine_dose_target` | ❓ | ❓ | ❓ | — | 👁 | ❓ |
| `chlorine_flow_rate` | ✅ | ✅ | — | — | ✅ | ❓ |
| `chlorine_production` | — | — | ✅ | — | — | — |
| `chlorine_pump_running` | ❓ | ❓ | — | — | ✅ `decode_v7_net` | ❓ |
| `configuration` | ✅ `decode_v7_by_unit_type_byte` | ✅ `decode_v7_by_unit_type_byte` | ✅ | ✅ `decode_v7_ph_and_oxy` | ✅ | ❓ `decode_v7_without_dose` |
| `dosing_delay` | ✅ | ✅ | ✅ | 👁 | 👁 | ❓ |
| `electrode_polarity` | — | — | ✅ | — | — | — |
| `electrolysis_running` | — | — | ✅ | — | — | — |
| `filtration_period_1_end` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_period_1_start` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_period_2_end` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_period_2_start` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_running` | 👁 | ✅ `decode_v7_menu_override` | ✅ | ✅ | — | ❓ |
| `filtration_schedule` | ✅ `decode_v7_home_a` | ✅ | ✅ | 👁 | — | ❓ |
| `flocculant_dose_target` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | — | ❓ `decode_v7_routed_by_byte37` |
| `flocculant_flow_rate` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | — | ❓ `decode_v7_routed_by_byte37` |
| `flocculant_pump_running` | ❓ | ❓ | ✅ | ✅ | — | ❓ |
| `free_chlorine` | ✅ | ✅ | ✅ | — | ✅ | ❓ |
| `free_chlorine_mv` | ✅ | ✅ | ✅ | — | ✅ | ❓ |
| `free_chlorine_target` | ✅ | ✅ | ✅ | — | 👁 | ❓ |
| `freeze_protection_enabled` | ✅ | ❓ | 🔍 | 🔍 | — | — |
| `heating_control_enabled` | ✅ | ❓ | 🔍 | 🔍 | — | — |
| `heating_running` | ❓ | ❓ | ❓ | ❓ | — | ❓ |
| `max_ph_doses` | 👁 | 👁 | ✅ | 👁 | — | ❓ |
| `max_refill_time` | ❓ | ❓ | ✅ | ❓ | — | ❓ |
| `oxygen_dose_target` | — | — | — | ✅ | — | — |
| `oxygen_flow_rate` | — | — | — | ✅ | — | — |
| `oxygen_pump_running` | — | — | — | ✅ | — | — |
| `ph` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `ph_minus_concentration` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `ph_minus_flow_rate` | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `ph_minus_pump_running` | ❓ | ❓ | ❓ | ✅ | ✅ `decode_v7_net` | ❓ |
| `ph_target` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `pool_volume` | ✅ | ✅ | ✅ | 👁 | 👁 | ❓ |
| `redox` | ❓ | ❓ | ✅ | — | ❓ | ❓ |
| `redox_target` | ❓ | ❓ | ✅ | — | ❓ | — |
| `refilling` | ✅ | ✅ | ❓ | ❓ | — | ❓ |
| `salinity` | — | — | ✅ | — | — | — |
| `serial_number` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service_menu_open` | — | ✅ | ✅ | 👁 | — | ❓ |
| `startup_delay` | ✅ | ✅ | ✅ | 👁 | ❓ | ❓ |
| `timestamp` | ✅ | ✅ | ✅ | ✅ | ❓ | ❓ |
| `variable_speed_pump_running` | ✅ | ✅ | ✅ | ❓ | — | — |
| `water_flow_to_probes` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `water_level` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_high_alarm` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_low_alarm` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_refill_start` | ❓ | ❓ | ✅ | ❓ | — | ❓ |
| `water_level_refill_stop` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_temperature` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `water_temperature_target` | ✅ | ✅ | ✅ | 👁 | — | ❓ |

## v8

| field | NET | SALT |
|---|---|---|
| `chlorine_flow_rate` | ❓ | — |
| `chlorine_pump_running` | ❓ | — |
| `configuration` | ✅ | ❓ |
| `dosing_delay` | ✅ | ❓ |
| `filtration_running` | ✅ | ❓ |
| `ph` | ✅ | ❓ |
| `ph_minus_flow_rate` | ❓ | ❓ |
| `ph_minus_pump_running` | ❓ | ❓ |
| `ph_target` | ✅ | ❓ |
| `pool_volume` | ✅ | ❓ |
| `redox` | ✅ | ❓ |
| `redox_target` | ✅ | ❓ |
| `serial_number` | ✅ | ✅ |
| `startup_delay` | ✅ | ❓ |
| `timestamp` | ✅ | ❓ |
| `water_flow_to_probes` | ✅ | ❓ |
| `water_temperature` | ✅ | ❓ |

## Help wanted

Every entry below is read today without a confirming capture.  If you own one of these units, a diagnostics download taken while the value is visible on the unit or in the Aseko Live app is exactly what is needed.

### v7 HOME firmware A

- `air_temperature` — unverified: bytes 23-24 = 0xFE70 (no air probe, the SALT marker) in every captured HOME frame, so no entity yet; the Aseko Live app shows air temperature on HOME units
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 was set on serial 110128063 with no matching alarm known in the app
- `algaecide_pump_running` — uncertain: byte[29] 0x20 assumed
- `backwash_running` — assumed: byte[29] 0x01, confirmed on SALT
- `chlorine_dose_target` — no evidence recorded
- `chlorine_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `flocculant_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_running` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; no HOME frame with the heater running (open item 9)
- `max_refill_time` — assumed: bytes 76-77 = 10800 s on serial 110128063, plausible (180 min); verified on SALT only
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `redox_target` — no evidence recorded
- `water_level_refill_start` — unconfirmed: byte[103] = 33 on serial 110128063 is read both as this threshold (cm) and as algaecide_flow_rate (ml/min); the two mappings cannot both be right

### v7 HOME firmware B

- `air_temperature` — unverified: bytes 23-24 = 0xFE70 (no air probe, the SALT marker) in every captured HOME frame, so no entity yet; the Aseko Live app shows air temperature on HOME units
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 was set on serial 110128063 with no matching alarm known in the app
- `algaecide_pump_running` — uncertain: byte[29] 0x20 assumed
- `backwash_running` — assumed: byte[29] 0x01, confirmed on SALT
- `chlorine_dose_target` — no evidence recorded
- `chlorine_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `flocculant_pump_running` — uncertain: byte[29] 0x20 assumed
- `freeze_protection_enabled` — unverified: byte[37] 0x80 read as on firmware A, no capture on B
- `heating_control_enabled` — unverified: byte[37] 0x08 read as on firmware A, no capture on B
- `heating_running` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; no HOME frame with the heater running (open item 9)
- `max_refill_time` — assumed: bytes 76-77 = 10800 s on serial 110128063, plausible (180 min); verified on SALT only
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `redox_target` — no evidence recorded
- `water_level_refill_start` — unconfirmed: byte[103] = 33 on serial 110128063 is read both as this threshold (cm) and as algaecide_flow_rate (ml/min); the two mappings cannot both be right

### v7 SALT

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set in the own SALT dumps, 37 frames 2026-08-08..28
- `chlorine_dose_target` — unverified: byte[53] for a DOSE unit; neither unit of the own SALT dumps, 37 frames 2026-08-08..28 is one
- `heating_running` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; never set in the own SALT dumps, whose unit has heating control OFF
- `ph_minus_pump_running` — unconfirmed: byte[29] 0x80; the bit was never set in the own SALT dumps, 37 frames 2026-08-08..28
- `refilling` — assumed: byte[29] 0x02, confirmed on HOME only; never set in the own SALT dumps, 37 frames 2026-08-08..28

### v7 OXY

- `air_temperature` — unverified: bytes 23-24 = 0xFE70 (no air probe, the SALT marker) in every captured OXY frame, so no entity yet; the Aseko Live app shows air temperature on Oxygen units
- `alarm_max_disinfection_dose` — unconfirmed: bytes 12-13 were 0x00 in every OXY frame; HOME encoding assumed
- `alarm_no_flow_to_probes` — unconfirmed: byte[13] was 0x00 in every OXY frame; confirmed on NET and HOME only
- `alarm_ph_dosing_ineffective` — unconfirmed: bytes 12-13 were 0x00 in every OXY frame; HOME encoding assumed
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set in the OXY frames
- `backwash_running` — assumed: byte[29] 0x01, confirmed on SALT
- `heating_running` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `max_refill_time` — assumed: bytes 76-77 = 3600 s on the Winnetoux OXY, plausible (60 min); verified on SALT only
- `ph_minus_concentration` — assumed: byte[112], confirmed on HOME
- `refilling` — assumed: byte[29] 0x02, confirmed on HOME
- `variable_speed_pump_running` — assumed: byte[22] 0x08, confirmed on HOME
- `water_level` — assumed: byte[27], confirmed on HOME
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded
- `water_level_refill_start` — unconfirmed: byte[103] is algaecide_flow_rate on OXY (confirmed, 60 ml/min); reading it as a level threshold too cannot be right
- `water_level_refill_stop` — no evidence recorded

### v7 NET

- `alarm_max_disinfection_dose` — unconfirmed: byte[12] is 0x00 on NET; HOME encodings assumed
- `alarm_ph_dosing_ineffective` — unconfirmed: byte[12] is 0x00 on NET; HOME encodings assumed
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set on NET
- `redox` — no evidence recorded
- `redox_target` — unverified: byte[53] * 10 on a REDOX NET; no such frame captured
- `startup_delay` — unverified: bytes 74-75 = 0xFFFF (not filled in) on the Issue #66 NET frame and on the ChemDoserProxy NET frame
- `timestamp` — n/a: bytes 6-11 are 0xFF on every NET frame, Home Assistant's clock is used instead

### v7 PROFI

- `alarm_max_disinfection_dose` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_no_flow_to_probes` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_ph_dosing_ineffective` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_rapid_ph_change` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_duration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_interval` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_start_time` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `chlorine_dose_target` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `chlorine_flow_rate` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `chlorine_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `configuration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `dosing_delay` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_period_1_end` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_period_1_start` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_period_2_end` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_period_2_start` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_schedule` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flocculant_dose_target` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md); the PROFI setpoints screen has a flocculant dose (ml/24 h m3) on its shared flocculant / algicide output
- `flocculant_flow_rate` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flocculant_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `free_chlorine` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `free_chlorine_mv` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `free_chlorine_target` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `heating_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `max_ph_doses` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `max_refill_time` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md); the 2021 PROFI manual lists a max. filling time
- `ph` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_minus_concentration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_minus_flow_rate` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_minus_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_target` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `pool_volume` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `redox` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `refilling` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `service_menu_open` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `startup_delay` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `timestamp` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_flow_to_probes` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_high_alarm` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_low_alarm` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_refill_start` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_refill_stop` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_temperature` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_temperature_target` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)

### v8 NET

- `chlorine_flow_rate` — assumed: not transmitted, 60 ml/min taken for consumption
- `chlorine_pump_running` — unconfirmed: outs[9] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running
- `ph_minus_flow_rate` — assumed: not transmitted, 60 ml/min taken for consumption
- `ph_minus_pump_running` — unconfirmed: outs[8] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running

### v8 SALT

- `configuration` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `dosing_delay` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `filtration_running` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph_minus_flow_rate` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph_minus_pump_running` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph_target` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `pool_volume` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `redox` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `redox_target` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `startup_delay` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `timestamp` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `water_flow_to_probes` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `water_temperature` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified

## Not located yet

Values these models have but nobody has found in the frame.  If you own one of these units, download diagnostics, change the setting on the unit, wait a minute and download again: the two frames show where it is.

### v7 SALT

- `freeze_protection_enabled` — not located: the unit's Configuration menu has Winter mode ON/OFF; HOME's byte[37] 0x80 is the algicide routing on SALT, so it lives elsewhere
- `heating_control_enabled` — not located: the unit's Configuration menu has Heating control ON/OFF; HOME's byte[37] 0x08 was clear in every own SALT frame with it OFF, the ON state was never captured

### v7 OXY

- `freeze_protection_enabled` — not located: the ASIN AQUA Oxygen manual describes freeze protection; no OXY frame has been compared with it
- `heating_control_enabled` — not located: the ASIN AQUA Oxygen manual describes heating control; no OXY frame has been compared with it

## Seen, not compared

Values captured from real units that nobody has yet checked against the unit display or the app.  If you own one of these units, comparing the entity with what the unit shows is all it takes.

### v7 HOME firmware A

- `filtration_running` — observed: byte[29] 0x08 clear while Aseko Live showed STOP, serial 110128063; the set state was not captured on firmware A
- `max_ph_doses` — observed: byte[115] = 20 on serial 110128063; the position is confirmed on SALT, the HOME setting was never compared

### v7 HOME firmware B

- `max_ph_doses` — observed: byte[115] = 20 on serial 110128063; the position is confirmed on SALT, the HOME setting was never compared

### v7 OXY

- `backwash_duration` — observed: byte[71] * 10 = 100 s on the Winnetoux OXY (serial 110157165); not compared with the app
- `backwash_interval` — observed: byte[68] = 0 (disabled) on the Winnetoux OXY (serial 110157165); not compared with the app
- `backwash_start_time` — observed: bytes 69-70 = 12:30 on the Winnetoux OXY (serial 110157165); not compared with the app
- `dosing_delay` — observed: bytes 106-107 = 120 s on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_period_1_end` — observed: bytes 58-59 = 16:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_period_1_start` — observed: bytes 56-57 = 08:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_period_2_end` — observed: bytes 62-63 = 22:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_period_2_start` — observed: bytes 60-61 = 18:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_schedule` — observed: byte[37] = 0x03 reads nonstop while the Winnetoux OXY ran filtration 24 h; no schedule transition captured
- `max_ph_doses` — observed: byte[115] = 30 on the Winnetoux OXY; the position is confirmed on SALT, the OXY setting was never compared
- `ph` — observed: bytes 14-15 = 7.17 on the Winnetoux OXY (serial 110157165); not compared with the app
- `ph_target` — observed: byte[52] / 10 = 7.2 on the Winnetoux OXY (serial 110157165); not compared with the app
- `pool_volume` — observed: bytes 92-93 = 41 m3 on the Winnetoux OXY (serial 110157165); not compared with the app
- `service_menu_open` — observed: byte[37] bit 0x04 clear in every OXY frame; the menu never captured open
- `startup_delay` — observed: bytes 74-75 = 240 s on the Winnetoux OXY; the analysis document mislabels byte[73]
- `water_flow_to_probes` — observed: byte[28] = 0xAA on the Winnetoux OXY (serial 110157165); not compared with the app
- `water_temperature` — observed: bytes 25-26 = 9.5 C on the Winnetoux OXY (serial 110157165); not compared with the app
- `water_temperature_target` — observed: byte[55] = 25 C on the Winnetoux OXY (serial 110157165); not compared with the app

### v7 NET

- `chlorine_dose_target` — observed: byte[53] = 5 ml/m3/h in DOSE mode (2026-04-07 capture); not compared with the app
- `dosing_delay` — observed: bytes 106-107 on the Issue #66 NET; not compared with the app
- `free_chlorine_target` — observed: byte[53] / 10 on the Issue #66 NET; not compared with the app
- `pool_volume` — observed: bytes 92-93 on the Issue #66 NET; not compared with the app

## Not mapped on any protocol

Fields that exist on `AsekoDevice` but that nothing knows how to read yet.

- `ph_plus_flow_rate`
- `ph_plus_pump_running`

## Totals

- features known: 65
- with a v7 reading: 63
- with a v8 reading: 17
- profiles: 10
