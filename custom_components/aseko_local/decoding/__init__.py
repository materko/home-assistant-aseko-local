"""Frame decoding by device profile.

A frame is read in three steps, none of which knows about the others'
internals:

1. ``frame.parse_frame`` turns the raw bytes into a protocol-specific *view*:
   a ``V7Frame`` over the 120-byte binary layout, or a ``V8Frame`` over the
   parsed sections of the text protocol.  This is the only per-protocol
   parsing in the integration.
2. ``profile.detect_profile`` reads protocol, model and firmware variant off
   that view and looks up one ``Profile``: the ordered list of features the
   device has, which reading (*variant*) each of them uses, and a few
   semantic flags.  Model knowledge lives in ``profiles/`` and nowhere else.
3. ``engine.decode`` walks the profile's plan and lets each feature's chosen
   variant read its value.  A feature is one field on ``AsekoDevice`` and
   lives in its own file under ``decoders/``, holding every known way to read
   that one value for both protocols.  A feature file knows nothing about
   models.

``aseko_decoder.AsekoDecoder`` and ``aseko_decoder_v8.AsekoV8Decoder`` are
thin facades over these three steps and remain the public entry points.
"""
