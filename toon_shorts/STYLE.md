# House style (default for every new video): multi-angle 2D

Approved reference: `ep_toronto_merge.py` (Toronto highway merge). Older single-angle reference:
`ep_signal.py` / `ep_distance.py`.

## Look
- 1080x1920 black frame, 16:9 scene band in the middle, bold white two-line caption above it.
- Flat 2D cartoon art with dark outlines, built on a real 3D->2D camera (`toronto.TCam`) so every
  shot can use a different angle.
- Mix of angles in every video:
  - game-style chase / follow cam (behind and above), with a small HUD where it fits
  - inside view (driver POV / character POV)
  - close-ups of faces and important objects (indicator, mirror, dash, phone...)
  - over-the-shoulder views
  - top (map) view for analysis: paths, gaps, distances, fields of view, highlighted with
    green (right) / red (wrong) overlays
- Real place when asked (e.g. Toronto: CN Tower skyline, Lake Ontario, Ontario road signs).
- Small "STEP n" badges + one short caption per step; a location tag at the start.

## Sound
- Sound effects only, synced to every action. No music bed, no talking, no bird/chirp ambience.
- Short emotional cues allowed: chimes / jingle on success, sad violin on failure.
- Keep ambience beds quiet so action sounds stand out (check the waveform).

## Quality checklist (before every final render)
1. Contact sheet of every shot + a frame every second of the whole video.
2. Check facts/logic (direction of travel, which mirror, signals, distances, timings).
3. Check faces read correctly (fear vs laugh, yawn, sleep, whistle pucker).
4. No dashboard side mirror inside the car; emergency lights small; nothing tiny or hidden.
5. Check the audio waveform: events must stand out from the bed.
