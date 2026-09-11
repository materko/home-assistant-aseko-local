"""Render the profiles as a human-readable support matrix (Markdown).

The matrix is generated, never edited by hand: ``scripts/generate_support_matrix.py``
writes it to ``docs/support_matrix.md`` and a test fails when the committed
file is out of date.  Everything in it comes from the profiles' feature
lists, overrides and ``evidence`` entries, so keeping those honest keeps the
document honest.
"""

from __future__ import annotations

from collections import defaultdict

from .decoders import ALL_FEATURES
from .feature import Feature
from .frame import Protocol
from .profile import Profile
from .profiles import ALL_PROFILES, FALLBACK_PROFILES

CONFIRMED = "✅"
UNSURE = "❓"
ABSENT = "—"

# Evidence entries start with one of these words.  Anything else counts as
# unsure, as does a listed feature with no evidence recorded at all.
_CONFIRMED_PREFIXES = ("confirmed", "derived")


def _status(profile: Profile, feature: type[Feature]) -> str:
    if feature not in profile.features:
        return ABSENT
    evidence = profile.evidence.get(feature, "")
    word = evidence.split(":", 1)[0].strip().lower()
    if any(word.startswith(prefix) for prefix in _CONFIRMED_PREFIXES):
        mark = CONFIRMED
    else:
        mark = UNSURE
    variant = profile.overrides.get(feature)
    return f"{mark} `{variant}`" if variant else mark


def _profiles_for(protocol: Protocol) -> list[Profile]:
    return [
        p for p in ALL_PROFILES if p.protocol is protocol and p not in FALLBACK_PROFILES
    ]


def _features_for(protocol: Protocol) -> list[type[Feature]]:
    listed = {f for p in _profiles_for(protocol) for f in p.features}
    return [f for f in ALL_FEATURES if f in listed]


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
        f"| {CONFIRMED} | read on this model, checked against the unit display or the Aseko Live app |"
    )
    w(
        f"| {UNSURE} | read on this model, but not yet confirmed by a capture — **a diagnostics dump would settle it** |"
    )
    w(
        f"| {ABSENT} | this model does not have the value, so no entity is created for it |"
    )
    w("| `decode_…` | the profile uses this reading instead of the protocol default |")
    w("")
    w(
        "Two further profiles exist that no unit is meant to decode with and that "
        "the tables leave out: **"
        + "** and **".join(p.name for p in FALLBACK_PROFILES)
        + "**.  The first reads what both HOME firmware revisions share while a "
        "frame with `byte[37]` unset cannot tell them apart; the second reads "
        "everything that has a generic v7 reading so an unmapped unit shows as much "
        "as possible in diagnostics, where it is reported as unrecognised."
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
    for profile in ALL_PROFILES:
        if profile in FALLBACK_PROFILES:
            continue
        unsure = [
            f
            for f in ALL_FEATURES
            if f in profile.features and _status(profile, f).startswith(UNSURE)
        ]
        if not unsure:
            continue
        w(f"### {profile.name}")
        w("")
        for feature in unsure:
            evidence = profile.evidence.get(feature, "no evidence recorded")
            w(f"- `{feature.field}` — {evidence}")
        w("")

    unmapped = [f for f in ALL_FEATURES if not f.protocols()]
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
