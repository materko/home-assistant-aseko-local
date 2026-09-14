"""Render the profiles as a human-readable support matrix (Markdown).

The matrix is generated, never edited by hand: ``scripts/generate_support_matrix.py``
writes it to ``docs/support_matrix.md`` and a test fails when the committed
file is out of date.  Everything in it comes from the profiles' feature
lists, overrides and ``evidence`` entries, so keeping those honest keeps the
document honest.
"""

from __future__ import annotations

from collections import defaultdict

from .feature import NOT_LOCATED, Feature
from .features import ALL_FEATURES
from .frames import Protocol
from .profile import Profile
from .profiles import ALL_PROFILES, FALLBACK_PROFILES

CONFIRMED = "✅"
OBSERVED = "👁"
UNSURE = "❓"
ABSENT = "—"
NOT_LOCATED_MARK = "🔍"

# Evidence entries start with one of these words.  Anything else counts as
# unsure, as does a listed feature with no evidence recorded at all.
_CONFIRMED_PREFIXES = ("confirmed", "derived")


def _status(profile: Profile, feature: type[Feature]) -> str:
    if feature not in profile.features:
        return ABSENT
    reading = profile.overrides.get(feature)
    if reading in NOT_LOCATED:
        return NOT_LOCATED_MARK
    evidence = profile.evidence.get(feature, "")
    word = evidence.split(":", 1)[0].strip().lower()
    if word.startswith("confirmed on "):
        # "confirmed on HOME: ..." confirms HOME, not the profile quoting it
        mark = CONFIRMED if _model_word(profile) in word.split() else UNSURE
    elif any(word.startswith(prefix) for prefix in _CONFIRMED_PREFIXES):
        mark = CONFIRMED
    elif word.startswith("observed"):
        mark = OBSERVED
    else:
        mark = UNSURE
    return f"{mark} `{reading}`" if reading else mark


def _model_word(profile: Profile) -> str:
    """The model as evidence names it: "salt", "home", "oxy", "net", "profi"."""
    return profile.name.split(" ", 1)[-1].lower()


def _profiles_for(protocol: Protocol) -> list[Profile]:
    return [
        p for p in ALL_PROFILES if p.protocol is protocol and p not in FALLBACK_PROFILES
    ]


def _features_for(protocol: Protocol) -> list[type[Feature]]:
    """Every feature some real profile of ``protocol`` lists, by field name."""
    listed = {f for p in _profiles_for(protocol) for f in p.features}
    return sorted(listed, key=lambda f: f.field)


def _help_section(w, mark: str) -> None:
    """List, per real profile, the features whose status carries ``mark``."""
    for profile in ALL_PROFILES:
        if profile in FALLBACK_PROFILES:
            continue
        listed = sorted(
            (f for f in profile.features if _status(profile, f).startswith(mark)),
            key=lambda f: f.field,
        )
        if not listed:
            continue
        w(f"### {profile.name}")
        w("")
        for feature in listed:
            evidence = profile.evidence.get(feature, "no evidence recorded")
            w(f"- `{feature.field}` — {evidence}")
        w("")


def render() -> str:
    """Return the whole document as Markdown."""
    out: list[str] = []
    w = out.append

    w("# Support matrix")
    w("")
    w(
        "What each decoding profile reads, and how sure we are.  Generated from "
        "`custom_components/aseko_local/decoding/profiles/` by "
        "`scripts/generate_support_matrix.py`; do not edit by hand."
    )
    w("")
    w(
        "A **profile** is one (protocol, model, firmware) combination.  A **feature** "
        "is one field on `AsekoDevice`, i.e. one value the integration can read."
    )
    w("")
    w("| Mark | Meaning |")
    w("|---|---|")
    w(
        f"| {CONFIRMED} | read on this model, checked against the unit display or the Aseko Live app on **this** model |"
    )
    w(
        f"| {OBSERVED} | seen repeatedly in captures from a real unit with consistent, plausible values, but not compared with the unit display or the app — **a glance at the unit would settle it** |"
    )
    w(
        f"| {UNSURE} | read on this model, but not checked on it: assumed, or confirmed only on another model — **a diagnostics dump would settle it** |"
    )
    w(
        f"| {ABSENT} | this model does not have the value, so no entity is created for it |"
    )
    w(
        f"| {NOT_LOCATED_MARK} | this model has the value (its menu or manual shows it), but where the frame carries it is not known yet: the entity exists and reads unknown — **a diagnostics dump before and after changing it on the unit would settle it** |"
    )
    w("| `decode_…` | the profile uses this reading instead of the protocol default |")
    w("")
    w(
        "A further profile exists that no unit is meant to decode with and that "
        "the tables leave out: **"
        + "** and **".join(p.name for p in FALLBACK_PROFILES)
        + "**.  It reads everything that has a generic v7 reading so an unmapped "
        "unit shows as much as possible in diagnostics, where it is reported as "
        "unrecognised."
    )
    w("")

    for protocol in Protocol:
        profiles = _profiles_for(protocol)
        features = _features_for(protocol)
        w(f"## {protocol.value}")
        w("")
        w(
            "| field | "
            + " | ".join(p.name.removeprefix(f"{protocol.value} ") for p in profiles)
            + " |"
        )
        w("|---|" + "---|" * len(profiles))
        for feature in features:
            cells = [_status(p, feature) for p in profiles]
            w(f"| `{feature.field}` | " + " | ".join(cells) + " |")
        w("")

    w("## Help wanted")
    w("")
    w(
        "Every entry below is read today without a confirming capture.  If you own "
        "one of these units, a diagnostics download taken while the value is "
        "visible on the unit or in the Aseko Live app is exactly what is needed."
    )
    w("")
    _help_section(w, UNSURE)

    w("## Not located yet")
    w("")
    w(
        "Values these models have but nobody has found in the frame.  If you own "
        "one of these units, download diagnostics, change the setting on the "
        "unit, wait a minute and download again: the two frames show where it is."
    )
    w("")
    _help_section(w, NOT_LOCATED_MARK)

    w("## Seen, not compared")
    w("")
    w(
        "Values captured from real units that nobody has yet checked against the "
        "unit display or the app.  If you own one of these units, comparing the "
        "entity with what the unit shows is all it takes."
    )
    w("")
    _help_section(w, OBSERVED)

    unmapped = sorted(
        (f for f in ALL_FEATURES if not f.protocols()), key=lambda f: f.field
    )
    if unmapped:
        w("## Not mapped on any protocol")
        w("")
        w("Fields that exist on `AsekoDevice` but that nothing knows how to read yet.")
        w("")
        for feature in unmapped:
            w(f"- `{feature.field}`")
        w("")

    by_protocol: dict[Protocol, int] = defaultdict(int)
    for feature in ALL_FEATURES:
        for protocol in feature.protocols():
            by_protocol[protocol] += 1
    w("## Totals")
    w("")
    w(f"- features known: {len(ALL_FEATURES)}")
    for protocol in Protocol:
        w(f"- with a {protocol.value} reading: {by_protocol[protocol]}")
    w(f"- profiles: {len(ALL_PROFILES)}")
    w("")
    return "\n".join(out)
