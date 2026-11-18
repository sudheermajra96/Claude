# toon_shorts

Procedural 2D cartoon generator for vertical (1080x1920) night-driving safety shorts.
Everything (art and sound effects) is generated in code; there are no asset files.

- `engine.py`: Cairo drawing (POV windshield, side/rear-view mirrors, dashboard,
  light stalk, pedals, driver character with expressions), keyframe/world system,
  numpy-synthesised SFX (engine, road roar, indicator ticks, stalk click, horn with
  doppler, tyre screech, pass-by whoosh, heartbeat, rewind), and the ffmpeg renderer.
- `ep_signal.py`: "ALWAYS signal before changing lanes!"
- `ep_distance.py`: "ALWAYS keep a safe distance!"
- `life.py`: daytime lifestyle scenes (bedroom with alarm, kitchen, desk, park run,
  checklist card, close-up), a posable rubber-hose character, day badge and energy bar
  overlays, and extra SFX (alarm, birds, crickets, footsteps, page flip, pen scribble,
  gulp, pop, sad trombone) plus an original soft music bed.
- `ep_5am.py`: "What happens if you wake up at 5 AM for 30 days?"

```
pip install pycairo scipy numpy   # plus ffmpeg on PATH and the Inter font
python3 ep_signal.py signal.mp4            # full video (~30 s render)
python3 ep_signal.py preview stills        # one PNG per shot
```

To make a new episode, copy an `ep_*.py` file and edit the caption, the `World`
keyframes (speed, lane position, vehicles, indicators), the shot list, the
overlays and the sound cue times.
