# Support matrix

What each decoding profile reads, and how sure we are.  Generated from `custom_components/aseko_local/decoding/profiles/` by `scripts/generate_support_matrix.py`; do not edit by hand.

A **profile** is one (protocol, model, firmware) combination.  A **feature** is one field on `AsekoDevice`, i.e. one value the integration can read.

| Mark | Meaning |
|---|---|
| ✅ | read on this model, checked against the unit display or the Aseko Live app |
| ❓ | read on this model, but not yet confirmed by a capture — **a diagnostics dump would settle it** |
| — | this model does not have the value, so no entity is created for it |
| `decode_…` | the profile uses this reading instead of the protocol default |

## v7

| field | HOME firmware A | HOME firmware B | HOME firmware not yet known | SALT | OXY | NET | PROFI | unknown unit type |
|---|---|---|---|---|---|---|---|---|
| `air_temperature` | — | — | — | ✅ | — | — | — | — |
| `alarm_no_flow_to_probes` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `alarm_orp_too_many_doses` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `alarm_ph_too_many_doses` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `alarm_rapid_ph_change` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| `algicide_pump_running` | ❓ | ❓ | ❓ | ✅ | ✅ `decode_v7_oxy` | — | — | — |
| `antifreeze_enabled` | ✅ | ❓ | ❓ | — | — | — | — | — |
| `backwash_active` | ❓ | ❓ | ❓ | ✅ | ❓ | — | ❓ | ❓ |
| `backwash_duration` | ❓ | ❓ | ❓ | ✅ | ❓ | — | ❓ | — |
| `backwash_every_n_days` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `backwash_time` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `cl_free` | ❓ | ❓ | ❓ | ❓ | — | ✅ | ❓ | ❓ |
| `cl_free_mv` | ❓ | ❓ | ❓ | ❓ | — | ✅ | ❓ | ❓ |
| `cl_pump_running` | ❓ | ❓ | ❓ | — | — | ✅ `decode_v7_net` | ❓ | — |
| `configuration` | ✅ `decode_v7_by_unit_type_byte` | ✅ `decode_v7_by_unit_type_byte` | ✅ `decode_v7_by_unit_type_byte` | ✅ | ✅ `decode_v7_ph_and_oxy` | ✅ | ❓ `decode_v7_without_dose` | ❓ `decode_v7_all_probes` |
| `delay_after_dose` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `delay_after_startup` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `electrolyzer_active` | — | — | — | ✅ | — | — | — | — |
| `electrolyzer_direction` | — | — | — | ❓ | — | — | — | — |
| `electrolyzer_power` | — | — | — | ✅ | — | — | — | — |
| `filtration_pump_running` | ❓ | ✅ `decode_v7_menu_override` | ❓ | ✅ | ✅ | — | ❓ | — |
| `filtration_schedule` | ✅ `decode_v7_home_a` | ✅ | ❓ | ✅ | ❓ | — | ❓ | — |
| `floc_pump_running` | ❓ | ❓ | ❓ | ✅ | ✅ | — | ❓ | — |
| `flowrate_algicide` | ✅ | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` |
| `flowrate_chlor` | ✅ | ✅ | ✅ | ❓ | — | ❓ | ❓ | ❓ |
| `flowrate_floc` | ✅ | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` | ❓ `decode_v7_routed_by_byte37` |
| `flowrate_oxy` | — | — | — | — | ✅ | — | — | — |
| `flowrate_ph_minus` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `heating_active` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | ❓ |
| `heating_control_enabled` | ✅ | ❓ | ❓ | — | — | — | — | — |
| `max_filling_time` | ❓ | ❓ | ❓ | ✅ | ❓ | — | — | — |
| `oxy_pump_running` | — | — | — | — | ✅ | — | — | — |
| `ph` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `ph_minus_concentration` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `ph_minus_pump_running` | ❓ | ❓ | ❓ | ❓ | ✅ | ✅ `decode_v7_net` | ❓ | — |
| `pool_volume` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `redox` | ❓ | ❓ | ❓ | ❓ | — | ❓ | ❓ | ❓ |
| `required_algicide` | ✅ | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | — | — |
| `required_cl_dose` | ❓ | ❓ | ❓ | ❓ | — | ❓ | ❓ | ❓ |
| `required_cl_free` | ❓ | ❓ | ❓ | ❓ | — | ❓ | ❓ | ❓ |
| `required_floc` | ✅ | ✅ | ✅ | ✅ `decode_v7_routed_by_byte37` | ✅ | ❓ `decode_v7_routed_by_byte37` | — | — |
| `required_oxy_dose` | — | — | — | — | ✅ | — | — | — |
| `required_ph` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `required_redox` | ❓ | ❓ | ❓ | ❓ | — | ❓ | — | ❓ |
| `required_water_temperature` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| `salinity` | — | — | — | ✅ | — | — | — | — |
| `serial_number` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `service_menu_open` | — | ✅ | — | ✅ | ❓ | — | ❓ | — |
| `start1` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `start2` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `stop1` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `stop2` | ❓ | ❓ | ❓ | ❓ | ❓ | — | ❓ | — |
| `timestamp` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `vsp_pump_running` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_filling_active` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_flow_to_probes` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| `water_level` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_level_filling_off` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_level_filling_on` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_level_high_alarm` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_level_low_alarm` | ✅ | ✅ | ✅ | ❓ | ❓ | — | ❓ | ❓ |
| `water_temperature` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |

## v8

| field | NET | SALT |
|---|---|---|
| `cl_pump_running` | ✅ | ✅ |
| `configuration` | ✅ | ❓ |
| `delay_after_dose` | ✅ | ✅ |
| `delay_after_startup` | ✅ | ✅ |
| `filtration_pump_running` | ✅ | ✅ |
| `flowrate_chlor` | ❓ | ❓ |
| `flowrate_ph_minus` | ❓ | ❓ |
| `ph` | ✅ | ✅ |
| `ph_minus_pump_running` | ✅ | ✅ |
| `pool_volume` | ✅ | ✅ |
| `redox` | ✅ | ✅ |
| `required_ph` | ✅ | ✅ |
| `required_redox` | ✅ | ✅ |
| `serial_number` | ✅ | ✅ |
| `timestamp` | ✅ | ✅ |
| `water_flow_to_probes` | ✅ | ✅ |
| `water_temperature` | ✅ | ✅ |

## Help wanted

Every entry below is read today without a confirming capture.  If you own one of these units, a diagnostics download taken while the value is visible on the unit or in the Aseko Live app is exactly what is needed.

### v7 HOME firmware A

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `algicide_pump_running` — uncertain: byte[29] 0x20 assumed
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `backwash_duration` — unverified: byte[71] * 10
- `backwash_every_n_days` — unverified: byte[68]
- `backwash_time` — unverified: bytes 69-70
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `cl_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `filtration_pump_running` — uncertain: byte[29] 0x08 assumed from SALT / OXY
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `max_filling_time` — assumed: bytes 76-77, confirmed on SALT
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_redox` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded

### v7 HOME firmware B

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `algicide_pump_running` — uncertain: byte[29] 0x20 assumed
- `antifreeze_enabled` — unverified: byte[37] 0x80 read as on firmware A, no capture on B
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `backwash_duration` — unverified: byte[71] * 10
- `backwash_every_n_days` — unverified: byte[68]
- `backwash_time` — unverified: bytes 69-70
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `cl_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `heating_control_enabled` — unverified: byte[37] 0x08 read as on firmware A, no capture on B
- `max_filling_time` — assumed: bytes 76-77, confirmed on SALT
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_redox` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded

### v7 HOME firmware not yet known

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `algicide_pump_running` — uncertain: byte[29] 0x20 assumed
- `antifreeze_enabled` — n/a: byte[37] is unset on every frame decoded with this profile
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `backwash_duration` — unverified: byte[71] * 10
- `backwash_every_n_days` — unverified: byte[68]
- `backwash_time` — unverified: bytes 69-70
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `cl_pump_running` — uncertain: byte[29] 0x40, port may be chlorine or OXY Pure
- `filtration_pump_running` — uncertain: byte[29] 0x08 assumed from SALT / OXY
- `filtration_schedule` — n/a: byte[37] is unset on every frame decoded with this profile
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `heating_control_enabled` — n/a: byte[37] is unset on every frame decoded with this profile
- `max_filling_time` — assumed: bytes 76-77, confirmed on SALT
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_redox` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded

### v7 SALT

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `backwash_every_n_days` — unverified: byte[68]
- `backwash_time` — unverified: bytes 69-70
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `electrolyzer_direction` — tentative: 0x50 = left from a single Apr 2 frame
- `flowrate_chlor` — unverified: byte[99], read as-is
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `ph_minus_concentration` — assumed: byte[112], confirmed on HOME only
- `ph_minus_pump_running` — unconfirmed: byte[29] 0x80, no frame with the pump running
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_redox` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded
- `vsp_pump_running` — assumed: byte[22] 0x08, confirmed on HOME only
- `water_filling_active` — assumed: byte[29] 0x02, confirmed on HOME only
- `water_level` — assumed: byte[27], confirmed on HOME only
- `water_level_filling_off` — no evidence recorded
- `water_level_filling_on` — no evidence recorded
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded

### v7 OXY

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `backwash_active` — assumed: byte[29] 0x01, confirmed on SALT
- `backwash_duration` — no evidence recorded
- `backwash_every_n_days` — no evidence recorded
- `backwash_time` — no evidence recorded
- `filtration_schedule` — assumed: bit flags as on SALT, no OXY capture of a transition
- `heating_active` — assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2
- `max_filling_time` — assumed: bytes 76-77, confirmed on SALT
- `ph_minus_concentration` — assumed: byte[112], confirmed on HOME
- `required_water_temperature` — unverified: byte[55], read as-is
- `service_menu_open` — assumed: byte[37] 0x04 as on SALT
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded
- `vsp_pump_running` — assumed: byte[22] 0x08, confirmed on HOME
- `water_filling_active` — assumed: byte[29] 0x02, confirmed on HOME
- `water_level` — assumed: byte[27], confirmed on HOME
- `water_level_filling_off` — no evidence recorded
- `water_level_filling_on` — no evidence recorded
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded

### v7 NET

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `flowrate_algicide` — unverified: byte[101] via byte[37] 0x80, as on SALT
- `flowrate_chlor` — unverified: byte[99]
- `flowrate_floc` — unverified: byte[101] via byte[37] 0x80 clear, as on SALT
- `redox` — no evidence recorded
- `required_algicide` — unverified: byte[54] via byte[37] 0x80, as on SALT
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_floc` — unverified: byte[54] via byte[37] 0x80 clear, as on SALT
- `required_redox` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is

### v7 PROFI

- `alarm_rapid_ph_change` — unconfirmed: byte[13] 0x08 from error_codes.md, no capture
- `backwash_active` — no evidence recorded
- `backwash_duration` — no evidence recorded
- `backwash_every_n_days` — no evidence recorded
- `backwash_time` — no evidence recorded
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `cl_pump_running` — uncertain: byte[29] 0x40 assumed
- `configuration` — uncertain: unit type 0x10 itself is unconfirmed; no DOSE bit
- `filtration_pump_running` — uncertain: byte[29] 0x08 assumed
- `filtration_schedule` — no evidence recorded
- `floc_pump_running` — uncertain: byte[29] 0x20 assumed
- `flowrate_algicide` — unverified: byte[101] via byte[37] 0x80, as on SALT
- `flowrate_chlor` — no evidence recorded
- `flowrate_floc` — unverified: byte[101] via byte[37] 0x80 clear, as on SALT
- `heating_active` — no evidence recorded
- `ph_minus_concentration` — no evidence recorded
- `ph_minus_pump_running` — uncertain: byte[29] 0x80 assumed
- `redox` — uncertain: bytes 18-19
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_water_temperature` — unverified: byte[55], read as-is
- `service_menu_open` — no evidence recorded
- `start1` — no evidence recorded
- `start2` — no evidence recorded
- `stop1` — no evidence recorded
- `stop2` — no evidence recorded
- `vsp_pump_running` — no evidence recorded
- `water_filling_active` — no evidence recorded
- `water_level` — no evidence recorded
- `water_level_filling_off` — no evidence recorded
- `water_level_filling_on` — no evidence recorded
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded

### v7 unknown unit type

- `alarm_no_flow_to_probes` — no evidence recorded
- `alarm_orp_too_many_doses` — no evidence recorded
- `alarm_ph_too_many_doses` — no evidence recorded
- `alarm_rapid_ph_change` — no evidence recorded
- `backwash_active` — no evidence recorded
- `cl_free` — no evidence recorded
- `cl_free_mv` — no evidence recorded
- `configuration` — no evidence recorded
- `delay_after_dose` — no evidence recorded
- `delay_after_startup` — no evidence recorded
- `flowrate_algicide` — no evidence recorded
- `flowrate_chlor` — no evidence recorded
- `flowrate_floc` — no evidence recorded
- `flowrate_ph_minus` — no evidence recorded
- `heating_active` — no evidence recorded
- `ph` — no evidence recorded
- `ph_minus_concentration` — no evidence recorded
- `pool_volume` — no evidence recorded
- `redox` — no evidence recorded
- `required_cl_dose` — no evidence recorded
- `required_cl_free` — no evidence recorded
- `required_ph` — no evidence recorded
- `required_redox` — no evidence recorded
- `required_water_temperature` — no evidence recorded
- `serial_number` — no evidence recorded
- `timestamp` — no evidence recorded
- `vsp_pump_running` — no evidence recorded
- `water_filling_active` — no evidence recorded
- `water_flow_to_probes` — no evidence recorded
- `water_level` — no evidence recorded
- `water_level_filling_off` — no evidence recorded
- `water_level_filling_on` — no evidence recorded
- `water_level_high_alarm` — no evidence recorded
- `water_level_low_alarm` — no evidence recorded
- `water_temperature` — no evidence recorded

### v8 NET

- `flowrate_chlor` — assumed: not transmitted, 60 ml/min taken for consumption
- `flowrate_ph_minus` — assumed: not transmitted, 60 ml/min taken for consumption

### v8 SALT

- `configuration` — assumed: same layout as NET; header type 105 only tells the model
- `flowrate_chlor` — assumed: not transmitted, 60 ml/min taken for consumption
- `flowrate_ph_minus` — assumed: not transmitted, 60 ml/min taken for consumption

## Not mapped on any protocol

Fields that exist on `AsekoDevice` but that nothing knows how to read yet.

- `flowrate_ph_plus`
- `ph_plus_pump_running`

## Totals

- features known: 64
- with a v7 reading: 62
- with a v8 reading: 17
- profiles: 10
