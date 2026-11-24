"""Square (1:1) scene band for the 1080x1920 Shorts frame.

The scene is drawn on a 1920 x 1920 logical canvas (instead of 1920 x 1080) and scaled to 1080 x 1080 in the middle
of the frame; the white title stays above it, in the same style as the 16:9 videos.
Call square_mode() after importing every drawing module: it sets SH = 1920 in all of them, so skies, grounds and
full-screen paints fill the taller canvas. Cameras must be made with cy = SQ_CY (horizon in the middle third).
"""
import os
import subprocess
import sys

import cairo

import engine
from engine import *

SQ = 1920.0                 # logical canvas size
SQ_PX = 1080.0              # on-screen size
SQ_Y = (1920 - SQ_PX) / 2 - 40          # top of the square band
SQ_CY = 900                 # default camera centre row on the square canvas


def square_mode():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, m in list(sys.modules.items()):
        f = getattr(m, '__file__', None) or ''
        if f.startswith(here) and getattr(m, 'SH', None) == 1080 and getattr(m, 'SW', None) == 1920:
            m.SH = int(SQ)


class SquareVideo(engine.Video):
    def frame(self, ctx, t):
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        n = len(self.caption)
        y0 = SQ_Y - 40 - (n - 1) * 70
        for i, line in enumerate(self.caption):
            text_center(ctx, line, W / 2, y0 + i * 70, 56)
        s = self.shot_at(t)
        ctx.save()
        ctx.rectangle(0, SQ_Y, W, SQ_PX)
        ctx.clip()
        ctx.translate(0, SQ_Y)
        k = SQ_PX / SQ
        ctx.scale(k, k)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        engine.SCENES[s.kind](ctx, self.world, t, t - s.start, s.kw)
        for t0, t1, fn in self.overlays:
            if t0 <= t < t1:
                fn(ctx, t - t0, t1 - t0)
        ctx.restore()


def sq_caption(text, size=86):
    return caption_in_scene(text, y=1800, size=size)


def sq_hud(ctx, w, t, unit='mph'):
    v = w.speed(t) * (2.237 if unit == 'mph' else 3.6)
    rrect(ctx, 1560, 1640, 310, 130, 34)
    setc(ctx, (0, 0, 0), 0.5)
    ctx.fill()
    text_center(ctx, f"{int(round(v))}", 1675, 1730, 84, (1, 1, 1))
    text_center(ctx, unit, 1800, 1730, 34, (0.85, 0.85, 0.9))


def check_sheet(video, out, cols=4):
    from PIL import Image
    import numpy as np
    tiles = []
    for s in video.shots:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        video.frame(cairo.Context(surf), s.start + s.dur * 0.6)
        a = np.ndarray((H, W, 4), np.uint8, surf.get_data())[..., [2, 1, 0]].copy()
        tiles.append(Image.fromarray(a).crop((0, int(SQ_Y) - 170, W, int(SQ_Y + SQ_PX))).resize((432, 500)))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (432 * cols, 500 * rows))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 432, (i // cols) * 500))
    sheet.save(out)
