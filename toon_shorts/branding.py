"""Channel art for "Road Rules Animated": YouTube banner (2560x1440) + profile icon (800x800),
plus previews of how they crop on desktop / mobile / TV and as a small circle."""
import math
import sys

import cairo
import numpy as np

import ep_toronto_merge as tm
from toronto import *

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
YEL = hexc('#ffd23f')


def title_text(ctx, x, y, size, maxw=1380):
    """'ROAD RULES' (yellow) + 'ANIMATED' (white), centred at x, baseline y."""
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    a, b = 'ROAD RULES ', 'ANIMATED'
    ctx.set_font_size(100)
    full = ctx.text_extents(a + b).x_advance
    size = min(size, 100 * maxw / full)
    ctx.set_font_size(size)
    wa, wb = ctx.text_extents(a).x_advance, ctx.text_extents(b).x_advance
    x0 = x - (wa + wb) / 2
    for txt, xx, col in ((a, x0, YEL), (b, x0 + wa, (1, 1, 1))):
        ctx.move_to(xx, y)
        ctx.text_path(txt)
        setc(ctx, OUTL)
        ctx.set_line_width(size * 0.16)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
        setc(ctx, col)
        ctx.fill()


def banner(path):
    W_, H_ = 2560, 1440
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W_, H_)
    ctx = cairo.Context(surf)
    ctx.save()
    ctx.scale(W_ / 1920, H_ / 1080)
    t = 20.2
    world = tm.world
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    cam = TCam((ex - 13 * math.sin(h) - 3.0, 6.2, ez - 13 * math.cos(h)), h + 0.12, 0.2, 1050, cy=560)
    draw_world(ctx, cam, world, t)
    ctx.restore()
    # safe area (1546 x 423, centred): darkened band + title + tagline
    sx, sy, sw, sh = (W_ - 1546) / 2, (H_ - 423) / 2, 1546, 423
    g = cairo.LinearGradient(0, sy - 60, 0, sy + sh + 60)
    g.add_color_stop_rgba(0, 0.03, 0.05, 0.12, 0.0)
    g.add_color_stop_rgba(0.2, 0.03, 0.05, 0.12, 0.55)
    g.add_color_stop_rgba(0.8, 0.03, 0.05, 0.12, 0.55)
    g.add_color_stop_rgba(1, 0.03, 0.05, 0.12, 0.0)
    ctx.set_source(g)
    ctx.rectangle(0, sy - 60, W_, sh + 120)
    ctx.fill()
    title_text(ctx, W_ / 2, sy + 200, 150, 1380)
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(50)
    tag = 'Traffic rules, the right way  •  in under 60 seconds'
    w = ctx.text_extents(tag).x_advance
    ctx.move_to(W_ / 2 - w / 2, sy + 300)
    setc(ctx, (1, 1, 1))
    ctx.show_text(tag)
    # three little "pill" chips
    chips = [('Driving', '#e23b3b'), ('Cycling', '#22a356'), ('Walking', '#3a7bd5')]
    ctx.set_font_size(40)
    widths = [ctx.text_extents(c[0]).x_advance + 70 for c in chips]
    x = W_ / 2 - (sum(widths) + 30 * 2) / 2
    for (label, col), wdt in zip(chips, widths):
        rrect(ctx, x, sy + 335, wdt, 64, 32)
        fill_stroke(ctx, hexc(col), (1, 1, 1), 4)
        ctx.move_to(x + 35, sy + 380)
        setc(ctx, (1, 1, 1))
        ctx.show_text(label)
        x += wdt + 30
    surf.write_to_png(path)
    return surf


def icon(path):
    N = 800
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, N, N)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, 0, N)
    g.add_color_stop_rgb(0, *hexc('#2f8fe0'))
    g.add_color_stop_rgb(0.55, *hexc('#bfe6ff'))
    ctx.set_source(g)
    ctx.paint()
    hy = 430
    setc(ctx, hexc('#6dbb5a'))
    ctx.rectangle(0, hy, N, N - hy)
    ctx.fill()
    vp = (400, hy)
    # road converging to the horizon
    poly(ctx, [(vp[0] - 18, hy), (vp[0] + 18, hy), (N + 160, N), (-160, N)])
    fill_stroke(ctx, hexc('#4b4f5c'), OUTL, 8)
    for k in range(5):
        u0, u1 = (k + 0.15) / 5, (k + 0.55) / 5
        y0, y1 = hy + (N - hy) * u0 ** 1.6, hy + (N - hy) * u1 ** 1.6
        w0, w1 = 4 + 22 * u0, 4 + 22 * u1
        poly(ctx, [(400 - w0, y0), (400 + w0, y0), (400 + w1, y1), (400 - w1, y1)])
        setc(ctx, YEL)
        ctx.fill()
    # sun
    glow(ctx, 590, 250, 200, hexc('#fff3b0'), 0.6)
    ellipse(ctx, 590, 250, 70, 70)
    setc(ctx, hexc('#ffe27a'))
    ctx.fill()
    # big red cartoon car (rear view) drawn with the video renderer
    cam = TCam((0.0, 1.8, -7.0), 0.0, 0.12, 1000, cx=400, cy=440)
    ctx.save()
    ctx.translate(0, 0)
    draw_car3(ctx, cam, 0.0, 0.0, 0.0, '#e23b3b', 0.0, False, 0.0, lw=9)
    ctx.restore()
    # thick white ring so it pops in the circular crop
    ctx.new_sub_path()
    ctx.arc(N / 2, N / 2, N / 2 - 14, 0, 2 * math.pi)
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(28)
    ctx.stroke()
    surf.write_to_png(path)
    return surf


def previews(bpath, ipath, out):
    from PIL import Image, ImageDraw
    b = Image.open(bpath).convert('RGB')
    i = Image.open(ipath).convert('RGB')
    W_, H_ = b.size
    desk = b.crop((0, (H_ - 423) // 2, W_, (H_ + 423) // 2)).resize((1280, 212))
    mob = b.crop(((W_ - 1546) // 2, (H_ - 423) // 2, (W_ + 1546) // 2, (H_ + 423) // 2)).resize((640, 175))
    tv = b.resize((640, 360))
    mask = Image.new('L', i.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, i.size[0], i.size[1]), fill=255)
    circ = Image.new('RGB', i.size, (255, 255, 255))
    circ.paste(i, (0, 0), mask)
    sheet = Image.new('RGB', (1320, 720), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    sheet.paste(desk, (20, 30))
    d.text((20, 8), 'Desktop (banner strip)', fill=(40, 40, 40))
    sheet.paste(mob, (20, 290))
    d.text((20, 268), 'Mobile (safe area)', fill=(40, 40, 40))
    sheet.paste(tv, (670, 290))
    d.text((670, 268), 'TV (full image)', fill=(40, 40, 40))
    for k, sz in enumerate((240, 98, 48)):
        sheet.paste(circ.resize((sz, sz)), (40 + k * 280, 480 + (240 - sz) // 2))
    d.text((40, 462), 'Icon at 240 / 98 / 48 px', fill=(40, 40, 40))
    sheet.save(out)


if __name__ == '__main__':
    bp, ip = f'{OUT}/road_rules_banner_2560x1440.png', f'{OUT}/road_rules_icon_800x800.png'
    banner(bp)
    icon(ip)
    previews(bp, ip, f'{OUT}/road_rules_preview.png')
