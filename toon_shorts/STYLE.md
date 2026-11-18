# House style (default for every new video)

Based on `ep_signal.py` and `ep_distance.py`, the approved reference videos.

- **Layout:** 1080x1920 black frame, a 16:9 scene band in the middle, bold white two-line
  caption directly above it (`Video(...)` defaults: `vertical=False`, `layered=False`).
- **Art:** flat 2D, dark outlines, simple shapes, no blur/cel-shading/dust layers.
- **Story:** WRONG way -> rewind -> RIGHT way, with small red WRONG / green RIGHT badges and
  very few in-scene captions.
- **Sound:** sound effects only, synced to every action. No music bed.
  Short emotional cues are allowed (chime on success, sad violin / sad trombone on failure).
- **No talking.** Original characters only.

Experimental modes (vertical full-frame, layered 2D, music beds) remain in the code but are
off by default and are not to be used unless asked for.
