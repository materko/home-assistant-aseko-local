# HOME "firmware A / B" is not a firmware difference: bit 0x40 of byte[37] is the Waterlevel setting

I ran a controlled test on my ASIN AQUA Salt (v7). I toggled one setting at a time on the unit's Configuration menu and put a timestamped marker in the frame log after each change, so every change can be tied to the frames around it. byte[37] behaved like this:

| Change on the unit | byte[37] |
|---|---|
| Heating control ON | bit **0x08** set (0xd3 → 0xdb), cleared again when switched off |
| Waterlevel OFF | bit **0x40** cleared (0xd7 → 0x93), set again when switched back on |
| Flow detection OFF | bit **0x02** cleared (0xd7 → 0xd1), set again when switched back on |
| Winter mode ON | bit 0x40 cleared too (the unit turns level control off in winter), and byte[22] bit 0x04 set |
| Opening the settings menu | bit 0x04 set |

So byte[37] seems to be one bit field of configuration flags, the same on SALT and HOME:

| Bit | Meaning |
|---|---|
| 0x01 | always set |
| 0x02 | Flow detection enabled |
| 0x04 | settings menu open / manual override |
| 0x08 | Heating control enabled |
| 0x10 | filtration period 1 enabled |
| 0x20 | filtration period 2 enabled |
| 0x40 | **Waterlevel (level meter) enabled** |
| 0x80 | antifreeze on HOME, shared-port algicide routing on SALT (unchanged by winter mode on SALT) |

That explains every HOME value we split into "A" and "B" without assuming two firmwares:

- **"Firmware A"** (0x40 always set): units with the level meter enabled.
  - 0x43 = nonstop with flow detection on.
  - 0x53 = timer period 1 enabled.
  - 0x47 / 0x57, the "transitional edit states", are simply the menu being open (0x04).
  - 0x41 / 0x45 / 0x49 (Issue #135) are a unit with flow detection off: 0x45 = menu open, 0x49 = heating control on.
- **"Firmware B"** (0x40 never set): a unit with no level meter configured. Its 0x01 / 0x11 / 0x31 / 0x35 are the same period bits and the same 0x04 override.
- **The antifreeze frame 0x81:** 0x40 disappears there because winter/antifreeze mode switches level control off, which I reproduced on the Salt.

This means we don't need two HOME profiles or firmware detection by byte[37]. One HOME profile with these bits covers all captured frames, and bit 0x40 becomes a new value, "water level meter enabled". Putting firmware knowledge into the decoder was exactly what I wanted to avoid, and it turns out it was never needed.

## Other SALT values found in the same test

- byte[22] bit 0x10 = backwash schedule enabled
- byte[22] bit 0x04 = winter mode active
- while winter mode is on, bytes 54 / 55 / 56–63 / 68 carry the winter program (algicide 2 ml, water 2 °C, filtration 12:00–12:15, backwash off) instead of the normal settings

## What would confirm it on HOME

A confirmation from a HOME owner would close this: toggle Waterlevel and Flow detection once each and download diagnostics after each change.
