"""Draw the app icons (black square, 'Fr' over 'En'). Usage: python3 tools/make_icons.py"""
from PIL import Image, ImageDraw, ImageFont

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def icon(size, path):
    s = size / 512
    img = Image.new("RGB", (size, size), "#000000")
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(BOLD, int(190 * s))
    d.text((size / 2, size * 0.40), "Fr", font=big, fill="#ffffff", anchor="mm")
    d.text((size / 2, size * 0.72), "En", font=big, fill="#8ab4ff", anchor="mm")
    img.save(path)


for n in (180, 192, 512):
    icon(n, f"icons/icon-{n}.png")
