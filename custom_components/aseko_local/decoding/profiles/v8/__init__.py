"""v8 profiles: the text protocol, firmware 8.x, port 51050.

One module per model (net, salt); this package keeps only what they share
-- the header type table and the common layout in ``common`` -- and the
lookup from a model to its profile.

Values v8 does not transmit -- pump flow rates above all -- are not listed
rather than invented, with one deliberate exception: the chlorine and
pH-minus flow rates are assumed at 60 ml/min so the consumption counters
have something to integrate.
"""

from __future__ import annotations

from ....models import AsekoDeviceType
from ...profile import Profile
from .common import MODEL_BY_HEADER_TYPE
from .net import NET
from .salt import SALT

BY_MODEL: dict[AsekoDeviceType, Profile] = {
    AsekoDeviceType.NET: NET,
    AsekoDeviceType.SALT: SALT,
}

__all__ = ["BY_MODEL", "MODEL_BY_HEADER_TYPE", "NET", "SALT"]
