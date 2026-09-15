"""Whether the filtration pump relay is on.

v7: byte[29] bit 0x08 on every model with a filtration output (confirmed on
OXY and SALT in every captured frame; assumed on HOME and PROFI).  v8: outs[2].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from ..feature import Feature
from .service_menu_open import ServiceMenuOpen

if TYPE_CHECKING:
    from ...models import AsekoDevice
    from ..frames import V7Frame, V8Frame


_LOGGER = logging.getLogger(__name__)

FILTRATION = 0x08


class FiltrationRunning(Feature):
    """v7: byte[29] bit 0x08.  v8: outs[2]."""

    field = "filtration_running"
    depends_on = (ServiceMenuOpen,)
    # only ``decode_v7_menu_override`` (HOME) reads it
    optional_depends_on = (ServiceMenuOpen,)

    @override
    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> bool:
        return bool(frame[29] & FILTRATION)

    def decode_v7_menu_override(self, frame: V7Frame, device: AsekoDevice) -> bool:
        """Return the relay bit, unless the settings menu says the pump was switched off.

        On HOME (Issue #133) byte[29] bit 0x08 stays set while the
        user has manually switched the pump off at the unit -- the override
        state lives in byte[37] bit 0x04, not in byte[29].  Trust the explicit
        flag over the schedule-driven bit.
        """
        running = bool(frame[29] & FILTRATION)
        if running and device.service_menu_open is True:
            _LOGGER.debug(
                "Manual OFF override active (byte[37] bit 0x04) - "
                "forcing filtration_running to False (byte[29]=0x%02x)",
                frame[29],
            )
            return False
        return running

    @override
    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> bool | None:
        return frame.flag("outs", 2)
