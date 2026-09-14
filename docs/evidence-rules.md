# Evidence rules

Every feature a profile lists carries one `evidence` string, e.g.

```python
evidence={                      # shape of the entries, not real findings
    FeatureA: "confirmed: byte[N] 0xMM matches the unit display (2026-09-11)",
    FeatureB: "confirmed on NET: byte[N] 0xMM (Issue #NNN)",
    FeatureC: "observed: bytes N-M, plausible values in 28 frames",
    FeatureD: "assumed: byte[N] as on OXY",
}
```

The word before the first `:` decides the mark in the generated
[support matrix](support_matrix.md); the rest is free text for people.

| Evidence starts with | Mark | Use it when |
|---|---|---|
| `confirmed` | ✅ | the decoded value was compared with the unit display or the Aseko Live app **on this model** |
| `derived` | ✅ | not compared on this model, but it follows from the protocol itself or from confirmed values — say which in the text; not a check of a real unit |
| `confirmed on <MODEL>` | ✅ only in `<MODEL>`'s column, ❓ elsewhere | the byte was confirmed on another model and this profile reads it the same way |
| `observed` | 👁 | seen repeatedly in real frames from this model with consistent, plausible values, but never compared with the unit |
| anything else (`assumed`, `unverified`, `uncertain`, …) or missing | ❓ | inherited from another model or an older decoder, nothing contradicts it yet |
| override `decode_v7_not_located` / `decode_v8_not_located` | 🔍 | the model has the value (menu, manual), but where the frame carries it is unknown; the entity exists and reads unknown |
| feature not listed in the profile | — | the profile does not read it: the model does not have it, or nobody has decoded it yet |

## Writing evidence

- Write what was checked, where and when: bytes/bits, date, issue or PR number,
  number of frames. Serial numbers of other people's units only when they are
  already public in an issue.
- Every profile spells its evidence out in full — nothing is inherited. If you
  copy a reading from another model, say so (`assumed: … as on OXY`) or use
  `confirmed on OXY:`.
- Upgrade a mark only with a capture: a marked test case (see the README) or a
  diagnostics download plus what the unit showed at that moment.
- A setting being present in the frame does not mean the hardware is fitted —
  water level, heating and the variable-speed pump can be enabled without the
  accessory. Evidence about a *setting* says so.
- When evidence changes, update the model's
  [device analysis](device%20analyzes/) too and regenerate the matrix:

```bash
python scripts/generate_support_matrix.py
```

`tests/test_support_matrix.py` fails while the committed matrix is out of date.
