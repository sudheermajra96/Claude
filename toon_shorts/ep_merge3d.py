"""3D episode: ALWAYS merge at highway speed! (three.js low-poly render + 2D overlays + synthesized SFX)."""
import glob
import os
import subprocess
import sys

from PIL import Image

from psych import *   # engine helpers, SFX (sad_violin, success_jingle...)

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 27.6
SPEED = Key([(0, 12), (11.4, 12), (12.4, 12), (14.6, 12), (19.0, 25), (27.6, 25)], 'lin')
CAPTION = ['ALWAYS merge at', 'highway speed!']
OVERLAYS = [
    (5.6, 7.3, caption_in_scene('No signal. Too slow.')),
    (6.9, 11.4, badge('WRONG', '#e0393e')),
    (12.4, 27.6, badge('RIGHT', '#22a356')),
    (12.9, 14.6, caption_in_scene('1. Signal early')),
    (16.0, 19.0, caption_in_scene('2. Match the speed')),
    (19.0, 21.6, caption_in_scene('3. Find a gap')),
    (21.6, 24.4, caption_in_scene('4. Merge smoothly')),
    (24.6, 27.6, caption_in_scene('Signal. Speed up. Merge.')),
]


def speed_hud(ctx, t):
    if 11.4 <= t < 12.4 or t >= 24.4:
        return
    kmh = SPEED(t) * 3.6
    col = hexc('#ff5a5a') if kmh < 70 else hexc('#22c35e')
    rrect(ctx, 1560, 50, 300, 110, 30)
    setc(ctx, (0, 0, 0), 0.55)
    ctx.fill()
    text_center(ctx, f"{int(kmh)}", 1660, 128, 72, col)
    text_center(ctx, 'km/h', 1785, 128, 34, (1, 1, 1))


def rewind_fx(ctx, t):
    if not (11.4 <= t < 12.4):
        return
    setc(ctx, (0.05, 0.05, 0.2), 0.3)
    ctx.paint()
    rnd = random.Random(int(t * 30))
    for _ in range(9):
        ctx.rectangle(0, rnd.uniform(0, SH), SW, rnd.uniform(3, 14))
        setc(ctx, (1, 1, 1), rnd.uniform(0.08, 0.3))
        ctx.fill()
    for i in range(2):
        x = 120 + i * 70
        poly(ctx, [(x + 70, 90), (x, 140), (x + 70, 190)])
        setc(ctx, (1, 1, 1))
        ctx.fill()
    text_center(ctx, "REWIND", 440, 162, 70)


def compose(frames_dir, out_path):
    world = World(dur=DUR, speed=SPEED, camx=const(0))
    wav = out_path + '.wav'
    write_wav(wav, sound(world))
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}', '-r', '30',
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '44100', '-c:a', 'aac', '-b:a', '192k',
           '-shortest', '-movflags', '+faststart', out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    files = sorted(glob.glob(os.path.join(frames_dir, '*.jpg')))
    for i, f in enumerate(files):
        t = i / 30
        img = Image.open(f).convert('RGBA')
        a = np.asarray(img)[..., [2, 1, 0, 3]].copy()
        fs = cairo.ImageSurface.create_for_data(memoryview(a), cairo.FORMAT_ARGB32, img.width, img.height)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        for j, line in enumerate(CAPTION):
            text_center(ctx, line, W / 2, SCENE_Y - 40 - (len(CAPTION) - 1 - j) * 70, 56)
        ctx.save()
        ctx.translate(0, SCENE_Y)
        ctx.scale(W / img.width, W / img.width)
        ctx.set_source_surface(fs, 0, 0)
        ctx.paint()
        ctx.restore()
        ctx.save()
        ctx.rectangle(0, SCENE_Y, W, SCENE_H)
        ctx.clip()
        ctx.translate(0, SCENE_Y)
        ctx.scale(SCALE, SCALE)
        rewind_fx(ctx, t)
        speed_hud(ctx, t)
        for t0, t1, fn in OVERLAYS:
            if t0 <= t < t1:
                fn(ctx, t - t0, t1 - t0)
        ctx.restore()
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()


def sound(world):
    m = Mixer(DUR)
    m.add(ambience(world, DUR, inside=0.9), 0, 1.6)
    # A: the wrong merge
    m.add(car_pass(2.4, 0.45, 105), 2.6, 0.9, np.linspace(-0.2, -0.8, int(2.4 * SR)))
    m.add(rumble(5.0), 3.2, 1.6, 0.4)
    m.add(click(), 6.85, 0.0)
    m.add(horn(1.2), 7.25, 0.75, 0.3)
    m.add(hp(noise(int(0.5 * SR)), 2500) * np.exp(-np.arange(int(0.5 * SR)) / SR / 0.15) * 0.4, 7.35, 0.8, 0.3)
    m.add(screech(1.9, 1100), 7.4, 0.7, 0.2)
    m.add(horn(0.35), 8.55, 0.7, 0.2)
    m.add(horn(0.9), 9.0, 0.7, 0.2)
    m.add(sad_violin(), 10.0, 0.8)
    m.add(rewind_sfx(1.0), 11.4, 1.0)
    # B: the right merge
    m.add(click(), 12.85, 0.8)
    indicator(m, 12.9, 24.0, 0.55, -0.2)
    m.add(click(), 24.02, 0.7)
    m.add(car_pass(2.4, 0.5, 110), 19.0, 0.9, np.linspace(-0.2, -0.7, int(2.4 * SR)))
    m.add(whoosh(1.0, 0.5), 21.9, 0.5, -0.3)
    m.add(success_jingle(), 24.4, 0.9)
    m.add(chime(), 24.7, 0.5)
    return m.out(DUR)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'merge3d.mp4'
    frames = out + '_frames'
    if '--skip-render' not in sys.argv:
        subprocess.run(['node', os.path.join(HERE, 'three', 'render.js'), frames], check=True)
    compose(frames, out)
