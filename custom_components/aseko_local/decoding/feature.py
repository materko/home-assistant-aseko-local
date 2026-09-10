"""The unit of decoding: one field on ``AsekoDevice``, every way to read it.

A ``Feature`` subclass names exactly one target field and carries the known
readings of that field as methods:

* ``decode_v7`` / ``decode_v8`` are the *default* reading for each protocol.
  A feature that has no reading for a protocol simply does not define the
  method, and no profile of that protocol may list it.
* Any further ``decode_<protocol>_<name>`` method is a named *variant* a
  profile can select instead of the default, for the models whose frame is
  encoded differently.  The feature file does not know which models those
  are; the profile does.

Every reading receives the frame view and the partially decoded device, so
a feature may read fields decoded before it.  Which fields those are is
declared in ``depends_on`` and honoured by the profile's ordering, never
checked at run time: a wrong order fails loudly at import, not quietly in
the field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from .frame import Protocol

if TYPE_CHECKING:
    from ..aseko_data import AsekoDevice
    from .frame import V7Frame, V8Frame


class Feature:
    """One target value and every known way to read it."""

    #: Name of the ``AsekoDevice`` field this feature fills.
    field: ClassVar[str]

    #: Features whose values this one reads off the device.  The profile
    #: orders its plan so these are decoded first.
    depends_on: ClassVar[tuple[type[Feature], ...]] = ()

    def decode_v7(self, frame: V7Frame, device: AsekoDevice) -> Any:
        """Default reading from a v7 frame.  Absent when v7 has none."""
        raise NotImplementedError

    def decode_v8(self, frame: V8Frame, device: AsekoDevice) -> Any:
        """Default reading from a v8 frame.  Absent when v8 has none."""
        raise NotImplementedError

    # -- introspection used by profiles ------------------------------------

    @classmethod
    def default_variant(cls, protocol: Protocol) -> str | None:
        """Name of the default reading for ``protocol``, or None if there is none."""
        name = f"decode_{protocol.value}"
        return name if cls.has_variant(name) else None

    @classmethod
    def has_variant(cls, name: str) -> bool:
        """Return True if ``name`` is a reading this feature actually defines."""
        own = getattr(cls, name, None)
        base = getattr(Feature, name, None)
        return callable(own) and own is not base

    @classmethod
    def variants(cls, protocol: Protocol | None = None) -> tuple[str, ...]:
        """All readings this feature defines, optionally for one protocol."""
        prefix = "decode_" if protocol is None else f"decode_{protocol.value}"
        return tuple(
            sorted(
                name
                for name in dir(cls)
                if name.startswith(prefix) and cls.has_variant(name)
            )
        )

    @classmethod
    def protocols(cls) -> tuple[Protocol, ...]:
        """Protocols this feature has at least one reading for."""
        return tuple(p for p in Protocol if cls.variants(p))
