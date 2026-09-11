# Support matrix

What each decoding profile reads, and how sure we are.  Generated from `custom_components/aseko_local/decoding/profiles/` by `scripts/generate_support_matrix.py`; do not edit by hand.

A **profile** is one (protocol, model, firmware) combination.  A **feature** is one field on `AsekoDevice`, i.e. one value the integration can read.

| Mark | Meaning |
|---|---|
| ✅ | read on this model, checked against the unit display or the Aseko Live app |
| 👁 | seen repeatedly in captures from a real unit with consistent, plausible values, but not compared with the unit display or the app — **a glance at the unit would settle it** |
| ❓ | read on this model, but never seen with a real value in any capture — **a diagnostics dump would settle it** |
| — | this model does not have the value, so no entity is created for it |
| `decode_…` | the profile uses this reading instead of the protocol default |

Two further profiles exist that no unit is meant to decode with and that the tables leave out: **v7 HOME firmware not yet known** and **v7 unknown unit type**.  The first reads what both HOME firmware revisions share while a frame with `byte[37]` unset cannot tell them apart; the second reads everything that has a generic v7 reading so an unmapped unit shows as much as possible in diagnostics, where it is reported as unrecognised.

## v7

| field | HOME firmware A | HOME firmware B | SALT | OXY | NET | PROFI |
|---|---|---|---|---|---|---|
| `air_temperature` | — | — | ✅ | — | — | — |
| `alarm_no_flow_to_probes` | ✅ | ✅ | ✅ | ❓ | ✅ | ❓ |
| `alarm_orp_too_many_doses` | ✅ | ✅ | ✅ | ❓ | ❓ | ❓ |
| `alarm_ph_too_many_doses` | ✅ | ✅ | ✅ | ❓ | ❓ | ❓ |
| `alarm_rapid_ph_change` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| `algicide_pump_running` | ❓ | ❓ | ✅ | ✅ `decode_v7_oxy` | — | — |
| `antifreeze_enabled` | ✅ | ❓ | — | — | — | — |
| `backwash_active` | ❓ | ❓ | ✅ | ❓ | — | ❓ |
| `backwash_duration` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `backwash_every_n_days` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `backwash_time` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `cl_free` | ✅ | ✅ | ✅ | — | ✅ | ❓ |
| `cl_free_mv` | ✅ | ✅ | ✅ | — | ✅ | ❓ |
| `cl_pump_running` | ❓ | ❓ | — | — | ✅ `decode_v7_net` | ❓ |
| `configuration` | ✅ `decode_v7_by_unit_type_byte` | ✅ `decode_v7_by_unit_type_byte` | ✅ | ✅ `decode_v7_ph_and_oxy` | ✅ | ❓ `decode_v7_without_dose` |
| `delay_after_dose` | ✅ | ✅ | ✅ | 👁 | 👁 | ❓ |
| `delay_after_startup` | ✅ | ✅ | ✅ | 👁 | 👁 | ❓ |
| `electrolyzer_active` | — | — | ✅ | — | — | — |
| `electrolyzer_direction` | — | — | ✅ | — | — | — |
| `electrolyzer_power` | — | — | ✅ | — | — | — |
| `filtration_pump_running` | 👁 | ✅ `decode_v7_menu_override` | ✅ | ✅ | — | ❓ |
| `filtration_schedule` | ✅ `decode_v7_home_a` | ✅ | ✅ | 👁 | — | ❓ |
| `floc_pump_running` | ❓ | ❓ | ✅ | ✅ | — | ❓ |
| `flowrate_algicide` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` |
| `flowrate_chlor` | ✅ | ✅ | ❓ | — | ✅ | ❓ |
| `flowrate_floc` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` |
| `flowrate_oxy` | — | — | — | ✅ | — | — |
| `flowrate_ph_minus` | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `heating_active` | ❓ | ❓ | ❓ | ❓ | — | ❓ |
| `heating_control_enabled` | ✅ | ❓ | — | — | — | — |
| `max_filling_time` | ❓ | ❓ | ✅ | ❓ | — | — |
| `oxy_pump_running` | — | — | — | ✅ | — | — |
| `ph` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `ph_minus_concentration` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `ph_minus_pump_running` | ❓ | ❓ | ❓ | ✅ | ✅ `decode_v7_net` | ❓ |
| `pool_volume` | ✅ | ✅ | ✅ | 👁 | 👁 | ❓ |
| `redox` | ❓ | ❓ | ✅ | — | ❓ | ❓ |
| `required_algicide` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | — |
| `required_cl_dose` | ❓ | ❓ | ❓ | — | 👁 | ❓ |
| `required_cl_free` | ✅ | ✅ | ✅ | — | 👁 | ❓ |
| `required_floc` | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | — |
| `required_oxy_dose` | — | — | — | ✅ | — | — |
| `required_ph` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `required_redox` | ❓ | ❓ | ✅ | — | ❓ | — |
| `required_water_temperature` | ✅ | ✅ | ✅ | 👁 | ❓ | ❓ |
| `salinity` | — | — | ✅ | — | — | — |
| `serial_number` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service_menu_open` | — | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_start1` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_start2` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_stop1` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `filtration_stop2` | ✅ | ✅ | ✅ | 👁 | — | ❓ |
| `timestamp` | ✅ | ✅ | ✅ | ✅ | ❓ | ❓ |
| `vsp_pump_running` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_filling_active` | ✅ | ✅ | ❓ | ❓ | — | ❓ |
| `water_flow_to_probes` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |
| `water_level` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_filling_off` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_filling_on` | ❓ | ❓ | ✅ | ❓ | — | ❓ |
| `water_level_high_alarm` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_level_low_alarm` | ✅ | ✅ | ✅ | ❓ | — | ❓ |
| `water_temperature` | ✅ | ✅ | ✅ | 👁 | ✅ | ❓ |

## v8

| field | NET | SALT |
|---|---|---|
| `cl_pump_running` | ❓ | ❓ |
| `configuration` | ✅ | ❓ |
| `delay_after_dose` | ✅ | ❓ |
| `delay_after_startup` | ✅ | ❓ |
| `filtration_pump_running` | ✅ | ❓ |
| `flowrate_chlor` | ❓ | ❓ |
| `flowrate_ph_minus` | ❓ | ❓ |
| `ph` | ✅ | ❓ |
| `ph_minus_pump_running` | ❓ | ❓ |
| `pool_volume` | ✅ | ❓ |
| `redox` | ✅ | ❓ |
| `required_ph` | ✅ | ❓ |
| `required_redox` | ✅ | ❓ |
| `serial_number` | ✅ | ✅ |
| `timestamp` | ✅ | ❓ |
| `water_flow_to_probes` | ✅ | ❓ |
| `water_temperature` | ✅ | ❓ |

## Help wanted

Every entry below is read today without a confirming capture.  If you own one of these units, a diagnostics download taken while the value is visible on the unit or in the Aseko Live app is exactly what is needed.

### v7 HOME firmware A

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 was set on serial 110128063 with no matching alarm known in the app
- `algicide_pump_running` — uncertain: byte[29] 0x20 assumed
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `cl_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; no HOME frame with the heater running (open item 9)
- `max_filling_time` — assumed: bytes 76-77 = 10800 s on serial 110128063, plausible (180 min); verified on SALT only
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_redox` — no evidence recorded
- `water_level_filling_on` — unconfirmed: byte[103] = 33 on serial 110128063 is read both as this threshold (cm) and as flowrate_algicide (ml/min); the two mappings cannot both be right

### v7 HOME firmware B

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 was set on serial 110128063 with no matching alarm known in the app
- `algicide_pump_running` — uncertain: byte[29] 0x20 assumed
- `antifreeze_enabled` — unverified: byte[37] 0x80 read as on firmware A, no capture on B
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `cl_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; no HOME frame with the heater running (open item 9)
- `heating_control_enabled` — unverified: byte[37] 0x08 read as on firmware A, no capture on B
- `max_filling_time` — assumed: bytes 76-77 = 10800 s on serial 110128063, plausible (180 min); verified on SALT only
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_redox` — no evidence recorded
- `water_level_filling_on` — unconfirmed: byte[103] = 33 on serial 110128063 is read both as this threshold (cm) and as flowrate_algicide (ml/min); the two mappings cannot both be right

### v7 SALT

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set in the own SALT dumps, 37 frames 2026-08-08..28
- `flowrate_chlor` — unverified: byte[99]; 0xFF in every frame of the own SALT dumps, 37 frames 2026-08-08..28 (no chlorine pump on a SALT)
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; never set in the own SALT dumps, 37 frames 2026-08-08..28
- `ph_minus_pump_running` — unconfirmed: byte[29] 0x80; the bit was never set in the own SALT dumps, 37 frames 2026-08-08..28
- `required_cl_dose` — unverified: byte[53] for a DOSE unit; neither unit of the own SALT dumps, 37 frames 2026-08-08..28 is one
- `water_filling_active` — assumed: byte[29] 0x02, confirmed on HOME only; never set in the own SALT dumps, 37 frames 2026-08-08..28

### v7 OXY

- `alarm_no_flow_to_probes` — unconfirmed: byte[13] was 0x00 in every OXY frame; confirmed on NET and HOME only
- `alarm_orp_too_many_doses` — unconfirmed: bytes 12-13 were 0x00 in every OXY frame; HOME encoding assumed
- `alarm_ph_too_many_doses` — unconfirmed: bytes 12-13 were 0x00 in every OXY frame; HOME encoding assumed
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set in the OXY frames
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `max_filling_time` — assumed: bytes 76-77 = 3600 s on the Winnetoux OXY, plausible (60 min); verified on SALT only
- `ph_minus_concentration` — assumed: byte[112], confirmed on HOME
- `vsp_pump_running` — assumed: byte[22] 0x08, confirmed on HOME
- `water_filling_active` — assumed: byte[29] 0x02, confirmed on HOME
- `water_level` — assumed: byte[27], confirmed on HOME
- `water_level_filling_off` — no evidence recorded
- `water_level_filling_on` — unconfirmed: byte[103] is flowrate_algicide on OXY (confirmed, 60 ml/min); reading it as a level threshold too cannot be right
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded

### v7 NET

- `alarm_orp_too_many_doses` — unconfirmed: byte[12] is 0x00 on NET; HOME encodings assumed
- `alarm_ph_too_many_doses` — unconfirmed: byte[12] is 0x00 on NET; HOME encodings assumed
- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md; never set on NET
- `flowrate_algicide` — unverified: byte[37] and byte[101] are 0xFF on every NET frame; no third pump
- `flowrate_floc` — unverified: byte[37] and byte[101] are 0xFF on every NET frame; no third pump
- `redox` — no evidence recorded
- `required_algicide` — unverified: byte[37] is 0xFF on every NET frame, so the shared-port reading never applies
- `required_floc` — unverified: byte[37] is 0xFF on every NET frame, so the shared-port reading never applies
- `required_redox` — unverified: byte[53] * 10 on a REDOX NET; no such frame captured
- `required_water_temperature` — n/a: byte[55] is 0xFF on NET, which has no water temperature setpoint
- `timestamp` — n/a: bytes 6-11 are 0xFF on every NET frame, Home Assistant's clock is used instead

### v7 PROFI

- `alarm_no_flow_to_probes` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_orp_too_many_doses` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_ph_too_many_doses` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `alarm_rapid_ph_change` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_active` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_duration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_every_n_days` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `backwash_time` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `cl_free` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `cl_free_mv` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `cl_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `configuration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `delay_after_dose` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `delay_after_startup` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_schedule` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `floc_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flowrate_algicide` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flowrate_chlor` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flowrate_floc` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `flowrate_ph_minus` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `heating_active` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_minus_concentration` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `ph_minus_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `pool_volume` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `redox` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `required_cl_dose` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `required_cl_free` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `required_ph` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `required_water_temperature` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `service_menu_open` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_start1` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_start2` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_stop1` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `filtration_stop2` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `timestamp` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `vsp_pump_running` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_filling_active` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_flow_to_probes` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_filling_off` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_filling_on` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_high_alarm` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_level_low_alarm` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)
- `water_temperature` — assumed: no real PROFI frame has been captured; layout inferred from the manual and the other models (profi_device_analysis.md)

### v8 NET

- `cl_pump_running` — unconfirmed: outs[9] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running
- `flowrate_chlor` — assumed: not transmitted, 60 ml/min taken for consumption
- `flowrate_ph_minus` — assumed: not transmitted, 60 ml/min taken for consumption
- `ph_minus_pump_running` — unconfirmed: outs[8] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running

### v8 SALT

- `cl_pump_running` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `configuration` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `delay_after_dose` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `delay_after_startup` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `filtration_pump_running` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `flowrate_chlor` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `flowrate_ph_minus` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `ph_minus_pump_running` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `pool_volume` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `redox` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `required_ph` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `required_redox` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `timestamp` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `water_flow_to_probes` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified
- `water_temperature` — assumed: only the header type (105) says SALT; the NET layout is taken over unverified

## Seen, not compared

Values captured from real units that nobody has yet checked against the unit display or the app.  If you own one of these units, comparing the entity with what the unit shows is all it takes.

### v7 HOME firmware A

- `filtration_pump_running` — observed: byte[29] 0x08 clear while Aseko Live showed STOP, serial 110128063; the set state was not captured on firmware A

### v7 OXY

- `backwash_duration` — observed: byte[71] * 10 = 100 s on the Winnetoux OXY (serial 110157165); not compared with the app
- `backwash_every_n_days` — observed: byte[68] = 0 (disabled) on the Winnetoux OXY (serial 110157165); not compared with the app
- `backwash_time` — observed: bytes 69-70 = 12:30 on the Winnetoux OXY (serial 110157165); not compared with the app
- `delay_after_dose` — observed: bytes 106-107 = 120 s on the Winnetoux OXY (serial 110157165); not compared with the app
- `delay_after_startup` — observed: bytes 74-75 = 240 s on the Winnetoux OXY; the analysis document mislabels byte[73]
- `filtration_schedule` — observed: byte[37] = 0x03 reads nonstop while the Winnetoux OXY ran filtration 24 h; no schedule transition captured
- `ph` — observed: bytes 14-15 = 7.17 on the Winnetoux OXY (serial 110157165); not compared with the app
- `pool_volume` — observed: bytes 92-93 = 41 m3 on the Winnetoux OXY (serial 110157165); not compared with the app
- `required_ph` — observed: byte[52] / 10 = 7.2 on the Winnetoux OXY (serial 110157165); not compared with the app
- `required_water_temperature` — observed: byte[55] = 25 C on the Winnetoux OXY (serial 110157165); not compared with the app
- `service_menu_open` — observed: byte[37] bit 0x04 clear in every OXY frame; the menu never captured open
- `filtration_start1` — observed: bytes 56-57 = 08:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_start2` — observed: bytes 60-61 = 18:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_stop1` — observed: bytes 58-59 = 16:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `filtration_stop2` — observed: bytes 62-63 = 22:00 in every frame on the Winnetoux OXY (serial 110157165); not compared with the app
- `water_flow_to_probes` — observed: byte[28] = 0xAA on the Winnetoux OXY (serial 110157165); not compared with the app
- `water_temperature` — observed: bytes 25-26 = 9.5 C on the Winnetoux OXY (serial 110157165); not compared with the app

### v7 NET

- `delay_after_dose` — observed: bytes 106-107 on the Issue #66 NET; not compared with the app
- `delay_after_startup` — observed: bytes 74-75 on the Issue #66 NET; not compared with the app
- `pool_volume` — observed: bytes 92-93 on the Issue #66 NET; not compared with the app
- `required_cl_dose` — observed: byte[53] = 5 ml/m3/h in DOSE mode (2026-04-07 capture); not compared with the app
- `required_cl_free` — observed: byte[53] / 10 on the Issue #66 NET; not compared with the app

## Not mapped on any protocol

Fields that exist on `AsekoDevice` but that nothing knows how to read yet.

- `flowrate_ph_plus`
- `ph_plus_pump_running`

## Totals

- features known: 64
- with a v7 reading: 62
- with a v8 reading: 17
- profiles: 10
