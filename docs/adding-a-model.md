# Adding a model or a value

A short recipe. The design behind it is in
[Decoding by device profile](decoding-by-device-profile.md); what counts as
proof is in [Evidence rules](evidence-rules.md).

## 1. Collect frames

An unmapped unit (v7 `byte[4]` or v8 header type the decoder does not know)
decodes with the *unknown* profile: it gets **no entities**, a warning is
logged, and the diagnostics download lists it under `unrecognised_devices`
with the annotated raw frame and the generic values.

Ask for (or record) marked test cases with the test cases card — one change on
the unit per marker — and the zip from **Download new**. The frame next to each
marker is the evidence. `python scripts/frame_log_tool.py DIAGNOSTICS.json --around N`
prints the frames around marker N.

## 2. Find the bytes

Compare the frames before and after each marker. Start from the closest known
model's [device analysis](device%20analyzes/) — most v7 models share the layout
and differ in a few bytes (`byte[29]` pump bits, `byte[37]` routing, `byte[53]`
setpoint, flow rates at 99–104). Write the findings into the model's device
analysis, using the common section layout.

## 3. Profile

- New v7 model: add the enum value to `AsekoDeviceType` (`models.py`), map the
  unit type byte in `_MODEL_BY_UNIT_TYPE` (`decoding/profile.py`), create
  `decoding/profiles/v7/<model>.py` and register it in `profiles/v7/__init__.py`
  (`BY_MODEL`) and `profiles/__init__.py` (`ALL_PROFILES`).
- New v8 product line: extend `model_from_header_type` in
  `profiles/v8/__init__.py` and add `profiles/v8/<model>.py`. A new firmware of
  a known line needs nothing — it reads with the line's profile.

A profile module is one `Profile(...)`:

```python
MODEL = Profile(
    name="v7 MODEL",
    protocol=Protocol.V7,
    model=AsekoDeviceType.MODEL,
    features=(*IDENTITY, *CHLORINE_PROBES, *FILTRATION, ...),  # groups from common.py
    overrides={AlgaecideFlowRate: "decode_v7_not_located"},
    evidence={...},          # one entry per listed feature
    flags=frozenset(),       # e.g. AsekoProfileFlag.DELAYS_IN_MINUTES
)
```

List only the features the model has. Use `overrides` only where a capture
shows this model reads a value differently; `decode_v7_not_located` for a value
the model has but nobody has found.

## 4. A new value (feature)

1. Add the field to `AsekoDevice` in `models.py`.
2. Add `decoding/features/<field>.py` with a `Feature` subclass: `field`,
   `decode_v7` / `decode_v8` defaults, named readings for model differences,
   `depends_on` / `optional_depends_on` for values it needs first. Return
   `NOT_PRESENT` when this unit does not have the value, `None` when the frame
   cannot say right now.
3. Add it to `ALL_FEATURES` in `features/__init__.py`, list it in the profiles that have it.
4. Add the entity description in `sensor.py` / `binary_sensor.py` with
   `feature="<field>"` and the translations in `translations/*.json`. Entities
   are created for every possible feature and enabled once a unit shows it —
   never change an existing entity key.

## 5. Tests and matrix

```bash
python scripts/generate_support_matrix.py
```

- Add the captured frame to `tests/test_decode_v7.py` (or `test_decode_v8.py`)
  with the values the unit showed.
- `tests/test_decoding_profiles.py` checks detection and profile consistency;
  `tests/test_support_matrix.py` checks the generated matrix is committed.
