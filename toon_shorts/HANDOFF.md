# Road Rules Animated: handoff for a new chat

Read this file first, then `STYLE.md`. Everything below is how the user and Claude made the videos so far.

## The channel
- YouTube Shorts channel **"Road Rules Animated"**: traffic and road-safety lessons for everyday drivers.
- Videos are **no talking, sound effects only, no music bed**. Short emotional cues are OK: chime or jingle on success,
  sad violin or sad trombone on failure, a heartbeat or riser for tension, a cinematic low "braam" hit.
  **Never bird or chirp sounds.**
- Every video must give **real value** (accurate, useful lesson). Creative and emotional or funny is welcome, but
  facts must be correct (cite a real rule or statistic when used; use fictional 555 phone numbers on signs).

## Look and format (current default = the latest video, `ep_aggressive.py`)
- 1080x1920 frame, **square 1:1 scene** in the middle (`sqkit.SquareVideo`), the **white 2-line title above it**
  (same style in every video). The older 16:9 band style (`Video`) is still available if asked.
- 2D cartoon art on a real 3D camera (multi-angle 2D+3D). **Cinematic look** via `cinekit.py`:
  sun lighting on all 3D faces, soft vehicle shadows, golden-hour haze, lens flare, colour grade, vignette, light
  film grain, speed streaks, camera shake. Use `FMUL = 1.4` (longer lenses) on the square canvas.
- Camera variety in every video: helicopter orbit, low tracking camera-car, telephoto from far ahead or behind,
  crane rising, dashboard camera facing the driver, rear-view mirror view, inside driver view, top or map view
  for the lesson, slow motion for the key moment.
- **Hook in the first 3 seconds** (flash-forward to the tensest moment + big question text), location tag,
  short captions, STEP badges for the right way, the wrong way first then a rewind (when it fits), and an end card
  with a **comment question** ("Ever been tailgated like this? Comment!").
- **Mention the location** in every video and use a **different city or road each time** (Canada / US / India so far).

## Hard rules learned from the user's feedback
- **Round tyres only** (`truckkit.wheel3`, `draw_car_round`), never square or flat wheels; tyres never drawn over the body.
- No side mirror drawn inside the car or on the dashboard; police lights small and realistic.
- Characters must never stick out of a car: occupants are drawn **only inside the window glass**
  (`draw_car_round(..., occ=...)`, `peoplekit.person3d`); close-ups clip everything to the window opening.
- Main character = the original curly-haired guy with glasses and a mustard jacket (`peoplekit` 'hero').
  **Do not use the user's own likeness.** Other cast: 'lady', 'husb', 'grandpa', 'medic', 'daughter'.
- Faces must read correctly (fear vs laugh, whistle = puckered mouth with notes).
- Check properly before rendering: no mistakes.

## Workflow (keep it short = fewer tokens)
1. Write `ep_<topic>.py` from the closest existing episode (copy its structure; for the cinematic square style copy `ep_aggressive.py`).
2. `python3 ep_x.py x verify`: numeric checks (bumper gaps, lateral clearance, people clear of cars, timings).
   Every vehicle pair must have a positive gap; near misses about 1.5–2 m.
3. `python3 ep_x.py <scratchpad>/c.png check`: ONE contact sheet; fix; then a few key stills only if needed.
4. Render in the background: `python3 ep_x.py <scratchpad>/x.mp4` (about 4–8 min).
5. Check a per-second strip (`ffmpeg fps=1 + tile`) and the waveform (`showwavespic`), then send the mp4.
6. Commit and push to the working branch after each video.

## Saving tokens and time (agreed with the user)
- **Start a new chat every 3–5 videos** (long chats make every message cost more). Paste the short message from the
  user plus this file.
- **Reuse locations**: make 3–5 videos per world before building a new place.
- **Reuse the camera library** (shots that already work in `ep_aggressive.py`: `heli`, `track`, `tele`, `crane`,
  `fixed`, `dash_face`, `interior_mirror`, slow motion `wt()`). Do not re-invent and re-tune cameras.
- One contact-sheet round + key stills instead of many rounds. Keep the numeric safety checks (cheap).
- The user gives topic + place + wrong-vs-right + end question up front, and says "don't ask, just make them one by one".
- Optional **fast mode**: turn off grain and flare on most shots to render near the old speed.
- TODO (good first task in a new chat): turn `ep_aggressive.py` into a reusable **template + camera library**
  (e.g. `cinetemplate.py`) so a new video only needs the traffic plan and captions.
- Expected cost: old videos 1x; first cinematic video about 2.5–3x usage; with template + library about 1.1–1.3x usage
  and about 1.5x render time.

## Code map (all in `toon_shorts/`)
- `engine.py` (frame, Video, Shot, Key, audio Mixer and SFX), `kit.py` (run/check helper, dash, SFX),
  `toronto.py` (TCam 3D camera, lbox, location_tag), `citykit.py` (Path/Mover, draw_scene, buildings, signs, hud),
  `truckkit.py` (wheel3, draw_car_round, tractor/trailer), `mkit.py` (Track agents, SegWorld, Street builder,
  m_cam/m_top/m_mirror, overlays), `peoplekit.py` (3D occupants + 2D close-up heads), `indiakit.py` (auto rickshaw,
  bikes, bus, cow, Indian street), `sqkit.py` (square 1:1 format), `cinekit.py` (cinematic look + cameras),
  `street.py` (police officer, ticket, siren), `life2.py`/`psych.py` (rewind, boing, sparkle, bell, sad violin, jingle).

## Videos already made (do not repeat; locations already used)
- Early: turn signal, following distance, 5 a.m., phone, spotlight, 3D merge, stop sign + police ticket.
- Series 1 (ep01–ep10): texting, seatbelt, yellow light, crosswalk, ambulance (old), overtaking, high beams, drowsy, rain, blind spot.
- Highway merge (Toronto, CN Tower), cycling + hand signals (Amsterdam), highway exit (Niagara / QEW),
  roundabout (Carmel), left turn (Chicago), 4-way stop (Vancouver), parallel parking (San Francisco),
  truck backing into a dock (Dallas), truck on a narrow bridge (Kananaskis), zipper merge (Montreal).
- Driver mistakes m01–m10: blind spot (Calgary), tailgating (Wellington County), rolling stop (Woodstock VT),
  no signal (Halifax), curve speed (Sea-to-Sky), phone (NYC), last-second exit (LA), blocking the crosswalk (Boston),
  truck no-zone (Amarillo), stopping gap (Seattle).
- Don't drive high, funny with police and impound (Toronto); India vs Canada split screen (Mumbai / Niagara Parkway);
  distracted by a woman in the next car, bumps the curb, funny (Miami Beach); make way for the ambulance,
  emotional (Ottawa).
- Emergencies: stalled on railroad tracks (Moose Jaw SK), flooded underpass (Houston), tire blowout (I-15 Las Vegas),
  brake failure on a hill (Duluth), night breakdown (401 Kingston), wrong-way driver (400 Barrie, winter).
- Square format: driving on the sidewalk to skip traffic, funny (Philadelphia); aggressive driver, cinematic (I-85 Atlanta).

## Topic ideas not done yet
Child or pet left in a hot car; ball rolls into the street; child behind a backing SUV; car seats done right;
door zone / Dutch reach; loose items become missiles; seat and airbag position; clear snow off the whole car;
seeing pedestrians at night; motorcycles look farther than they are; construction zones; rubbernecking (funny);
road rage (engage vs de-escalate); yield to the bus; phantom traffic jams; Move Over law; traffic lights out = 4-way stop;
school bus stop arm; black ice on bridges; fog (low beams); sun glare; left-lane camping; weave lanes; hydroplaning.
