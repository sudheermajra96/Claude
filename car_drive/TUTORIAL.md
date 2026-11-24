# How to make this 3D car driving video

You get a short 3D city driving clip from a chase camera. It renders in a few minutes on an ordinary computer, with no game engine or 3D software. The scene is built in code with **Three.js**, a browser 3D library. **Playwright** drives a headless browser to capture the frames, and **ffmpeg** joins them into an MP4.

## 1. Install the tools
You need Node.js 18 or newer and ffmpeg.
```bash
npm i three@0.160.0 playwright
npx playwright install chromium      # one-time browser download
cp node_modules/three/build/three.min.js .
```

## 2. Render the video
```bash
node rec.js 300        # 300 frames at 30fps = 10 seconds
```
The output is `car_drive_square.mp4` (1080×1080). A 10-second clip takes about 2–3 minutes.

To preview the scene, open `scene.html` in a browser. To change the resolution, add `?w=1920&h=1080` to the URL in `rec.js` and set the matching viewport there.

## 3. How it works
| Part | What it does (in `scene.html`) |
|---|---|
| Road, sidewalks, buildings | Simple boxes and planes. Textures (asphalt, lane lines, windows, paving) are drawn on a `<canvas>` in code, so there are no image files. |
| Cars | Built from boxes: body, cabin, wheels, lights. `car(color, type)` makes a sedan, hatchback, van, sports car, bus or truck. |
| Lighting | A warm low sun with soft shadows, sky light, ACES tone mapping and a sky gradient with distance fog. |
| Driving | `plan` lists the lane changes as `[time, lane]`. `px(t)` blends smoothly between lanes. |
| Traffic | Cars are placed so they never sit in the player's lane at the moment the player passes them. |
| Recording | `renderFrame(t)` draws the exact frame for time `t`, so the video is smooth and identical on every run, however slow the computer is. |

## 4. Easy changes
- **Car color:** `car(0xd95a1a,'hatch')` → pick any hex color or type
- **Speed:** `const V=24` (metres per second; 24 is about 86 km/h)
- **Length:** `const T=10` and the frame count passed to `rec.js`
- **Camera:** `cam.position.set(cx, 4.8, pz+9.5)`, where the second number is height and the third is distance behind the car
- **Time of day:** sun color/intensity (`DirectionalLight`), sky gradient colors, fog color
- **Lane changes:** edit the `plan` array
