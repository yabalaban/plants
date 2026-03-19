"""Generate PWA app icons for Plant Tracker."""
from PIL import Image, ImageDraw, ImageFilter
import math

RENDER = 2048
OUTPUT_DIR = '/home/pi/plants/frontend/static'

# App color palette
BG = (26, 31, 22)           # #1a1f16
LEAF = (148, 185, 112)      # slightly more saturated sage
LEAF_LIGHT = (180, 210, 150)
LEAF_DARKER = (115, 155, 80)
ACCENT_GLOW = (168, 198, 134)


def w_at(t, max_w):
    """Leaf half-width at position t (0=base, 1=tip)."""
    return max_w * math.sin(math.pi * t) * max(0, 1 - t ** 2.5)


def to_xy(along, across, rot, ox, oy):
    """Convert leaf-local coords to canvas coords."""
    x = ox + along * math.cos(rot) - across * math.sin(rot)
    y = oy + along * math.sin(rot) + across * math.cos(rot)
    return (x, y)


def build_leaf_outline(leaf_len, leaf_w, rot, ox, oy, steps=300):
    outline = []
    for i in range(steps + 1):
        t = i / steps
        a = -leaf_len / 2 + t * leaf_len
        outline.append(to_xy(a, w_at(t, leaf_w) / 2, rot, ox, oy))
    for i in range(steps, -1, -1):
        t = i / steps
        a = -leaf_len / 2 + t * leaf_len
        outline.append(to_xy(a, -w_at(t, leaf_w) / 2, rot, ox, oy))
    return outline


img = Image.new('RGBA', (RENDER, RENDER), BG + (255,))

# Subtle radial glow
glow = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
r = int(RENDER * 0.38)
cx, cy = RENDER // 2, int(RENDER * 0.47)
gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT_GLOW + (18,))
glow = glow.filter(ImageFilter.GaussianBlur(radius=int(RENDER * 0.18)))
img = Image.alpha_composite(img, glow)

# === Main leaf (large, fills ~65% of icon) ===
leaf_len = RENDER * 0.62
leaf_w = RENDER * 0.27
rot = math.radians(-35)
ox, oy = RENDER * 0.50, RENDER * 0.47
outline = build_leaf_outline(leaf_len, leaf_w, rot, ox, oy)

# Drop shadow
shadow = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
ImageDraw.Draw(shadow).polygon(
    [(x + 35, y + 35) for x, y in outline], fill=(0, 0, 0, 50)
)
shadow = shadow.filter(ImageFilter.GaussianBlur(55))
img = Image.alpha_composite(img, shadow)

# Leaf body
layer = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
d.polygon(outline, fill=LEAF + (255,))

# Subtle inner gradient - lighter at the tip area
highlight = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
hd = ImageDraw.Draw(highlight)
# Light ellipse near the upper portion of the leaf
tip_x, tip_y = to_xy(leaf_len * 0.15, 0, rot, ox, oy)
hr = int(RENDER * 0.18)
hd.ellipse([tip_x - hr, tip_y - hr, tip_x + hr, tip_y + hr],
           fill=LEAF_LIGHT + (35,))
highlight = highlight.filter(ImageFilter.GaussianBlur(int(RENDER * 0.08)))
# Mask highlight to leaf shape
leaf_mask = Image.new('L', (RENDER, RENDER), 0)
ImageDraw.Draw(leaf_mask).polygon(outline, fill=255)
highlight.putalpha(Image.fromarray(
    __import__('numpy').minimum(
        __import__('numpy').array(highlight.getchannel('A')),
        __import__('numpy').array(leaf_mask)
    )
)) if False else None  # skip numpy dep, just composite
layer = Image.alpha_composite(layer, highlight)

# Midrib (softer, more subtle)
N = 200
for i in range(N):
    t = i / N
    a1 = -leaf_len / 2 + t * leaf_len
    a2 = -leaf_len / 2 + (i + 1) / N * leaf_len
    alpha = int(80 + 60 * (1 - t))
    width = max(2, int(8 * (1 - t * 0.85)))
    d.line(
        [to_xy(a1, 0, rot, ox, oy), to_xy(a2, 0, rot, ox, oy)],
        fill=LEAF_LIGHT + (alpha,),
        width=width,
    )

# Secondary veins (subtle, fewer)
for v in range(4):
    tp = 0.20 + v * 0.17
    ap = -leaf_len / 2 + tp * leaf_len
    vw = w_at(tp, leaf_w) * 0.38
    va = math.radians(42 + v * 3)
    for s in [-1, 1]:
        start = to_xy(ap, 0, rot, ox, oy)
        end = (
            start[0] + vw * math.cos(rot + s * va),
            start[1] + vw * math.sin(rot + s * va),
        )
        d.line(
            [start, end],
            fill=LEAF_LIGHT + (35,),
            width=max(1, int(4 * (1 - tp))),
        )

img = Image.alpha_composite(img, layer)

# === Small accent leaf (adds visual interest) ===
small_len = RENDER * 0.28
small_w = RENDER * 0.13
small_rot = math.radians(-65)
small_ox = RENDER * 0.38
small_oy = RENDER * 0.62
small_outline = build_leaf_outline(small_len, small_w, small_rot, small_ox, small_oy)

# Small leaf shadow
sm_shadow = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
ImageDraw.Draw(sm_shadow).polygon(
    [(x + 20, y + 20) for x, y in small_outline], fill=(0, 0, 0, 35)
)
sm_shadow = sm_shadow.filter(ImageFilter.GaussianBlur(30))
img = Image.alpha_composite(img, sm_shadow)

# Small leaf body (slightly darker for depth)
sm_layer = Image.new('RGBA', (RENDER, RENDER), (0, 0, 0, 0))
smd = ImageDraw.Draw(sm_layer)
smd.polygon(small_outline, fill=LEAF_DARKER + (230,))

# Small leaf midrib
for i in range(100):
    t = i / 100
    a1 = -small_len / 2 + t * small_len
    a2 = -small_len / 2 + (i + 1) / 100 * small_len
    smd.line(
        [to_xy(a1, 0, small_rot, small_ox, small_oy),
         to_xy(a2, 0, small_rot, small_ox, small_oy)],
        fill=LEAF + (int(60 + 40 * (1 - t)),),
        width=max(1, int(5 * (1 - t * 0.9))),
    )

img = Image.alpha_composite(img, sm_layer)

# Export
final = img.convert('RGB')
for name, size in [
    ('icon-512.png', 512),
    ('icon-192.png', 192),
    ('apple-touch-icon.png', 180),
    ('favicon-32.png', 32),
]:
    final.resize((size, size), Image.LANCZOS).save(f'{OUTPUT_DIR}/{name}')
    print(f'Saved {name} ({size}x{size})')

# Generate .ico with multiple sizes (16 + 32)
ico_16 = final.resize((16, 16), Image.LANCZOS)
ico_32 = final.resize((32, 32), Image.LANCZOS)
ico_16.save(f'{OUTPUT_DIR}/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32)],
            append_images=[ico_32])
print('Saved favicon.ico (16+32)')
