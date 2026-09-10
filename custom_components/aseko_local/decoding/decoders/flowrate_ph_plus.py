"""Configured pH-plus pump flow rate (ml/min).

Not mapped: byte[97] is the suspected position but no frame has confirmed
it, so the field stays None everywhere and no profile lists this feature.
"""

from __future__ import annotations

from ..feature import Feature


class FlowratePhPlus(Feature):
    """No known reading yet."""

    field = "flowrate_ph_plus"
