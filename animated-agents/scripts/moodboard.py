#!/usr/bin/env python3
"""Read a moodboard and turn it into colours the rest of the pipeline can use.

Usage:
  python moodboard.py --in moodboard/ --out <kit>/brief [--colors 8]

Writes to --out:
  palette.png   the moodboard as a contact sheet with the extracted palette underneath (show this to the user)
  palette.json  {"palette": [...], "body_gradient": {...}, "effect_colors": [...], "background": {...}}

Colours are measured from the images (k-means on pixels), sorted dark to light. The suggestions:
  body_gradient   top / middle / bottom colours for the prompt's colour sentence (light, mid, deeper tones)
  effect_colors   5 to 7 accent colours with enough contrast against the background (for UI around the agents)
  background      a soft light and a dark surface colour that suit the palette
These are starting points for the style brief; the user should confirm or adjust them.
"""
import argparse, colorsys, json, os
import numpy as np
from PIL import Image, ImageDraw


def load(paths):
    ims = []
    for p in paths:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((400, 400))
            ims.append((os.path.basename(p), im))
        except Exception as e:
            print("  skipped", p, e)
    return ims


def kmeans(px, k, iters=18, seed=3):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), k, replace=False)].astype(np.float32)
    for _ in range(iters):
        d = ((px[:, None, :] - c[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            m = px[lab == j]
            if len(m):
                c[j] = m.mean(0)
    counts = np.bincount(lab, minlength=k)
    return c, counts


def hexc(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def hls(c):
    return colorsys.rgb_to_hls(*(np.array(c) / 255))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--colors", type=int, default=8)
    a = ap.parse_args()
    paths = []
    for p in a.src:
        if os.path.isdir(p):
            paths += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        else:
            paths.append(p)
    ims = load(paths)
    if not ims:
        raise SystemExit("No moodboard images found.")
    px = np.concatenate([np.asarray(im).reshape(-1, 3) for _, im in ims]).astype(np.float32)
    l = 0.299 * px[:, 0] + 0.587 * px[:, 1] + 0.114 * px[:, 2]
    keep = (l > 22) & (l < 250)  # drop plain black/white backgrounds so they don't swamp the palette
    if keep.mean() > 0.05:
        px = px[keep]
    px = px[np.random.default_rng(1).choice(len(px), min(len(px), 60000), replace=False)]
    cents, counts = kmeans(px, a.colors)
    order = np.argsort([lum(c) for c in cents])
    pal = [(cents[i], int(counts[i])) for i in order]
    cols = [hexc(c) for c, _ in pal]
    # body gradient: a light top, a mid tone, a deeper bottom (skip near-black and near-white extremes)
    usable = [c for c, _ in pal if 35 < lum(c) < 248] or [c for c, _ in pal]
    top, mid, bot = usable[-1], usable[len(usable) // 2], usable[max(0, len(usable) // 4)]
    # effect colours: the more saturated mid tones, spread across hues
    colourful = [c for c, _ in pal if 50 < lum(c) < 235 and hls(c)[2] > 0.12]
    effects = [hexc(c) for c in sorted(colourful, key=lambda c: hls(c)[0])[:7]]  # spread by hue
    if len(effects) < 5:  # muted moodboards: deepen and enrich the palette's own tones
        base = [c for c, _ in pal if 40 < lum(c) < 240] or [c for c, _ in pal]
        extra = []
        for c in base:
            h, l2, s2 = hls(c)
            for dl in (-0.12, 0.0, 0.08):
                r, g, b = colorsys.hls_to_rgb(h, min(0.8, max(0.3, l2 + dl)), min(1.0, s2 * 1.8 + 0.12))
                extra.append(hexc((r * 255, g * 255, b * 255)))
        effects = list(dict.fromkeys(effects + extra))[:6]
    if len(effects) < 5:
        effects = (effects + cols)[:5]
    # backgrounds: a very soft light version of the lightest colour, and a deep version of the darkest
    light = np.clip(np.array(pal[-1][0]) * 0.25 + 255 * 0.75, 0, 255)
    dark = np.clip(np.array(pal[0][0]) * 0.35 + np.array([14, 16, 24]) * 0.65, 0, 255)
    out = {"palette": cols, "body_gradient": {"top": hexc(top), "middle": hexc(mid), "bottom": hexc(bot)},
           "effect_colors": effects, "background": {"light": hexc(light), "dark": hexc(dark)},
           "sources": [n for n, _ in ims]}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "palette.json"), "w"), indent=2)
    # contact sheet with swatches
    tw, cols_n = 220, min(4, len(ims))
    rows = (len(ims) + cols_n - 1) // cols_n
    sheet = Image.new("RGB", (tw * cols_n, tw * rows + 150), "white")
    for i, (_, im) in enumerate(ims):
        t = im.copy(); t.thumbnail((tw, tw))
        sheet.paste(t, (tw * (i % cols_n) + (tw - t.width) // 2, tw * (i // cols_n) + (tw - t.height) // 2))
    d = ImageDraw.Draw(sheet)
    sw = sheet.width / len(cols)
    for i, c in enumerate(cols):
        d.rectangle([i * sw, tw * rows + 10, (i + 1) * sw - 4, tw * rows + 100], fill=c)
        d.text((i * sw + 4, tw * rows + 108), c, fill=(40, 40, 40))
    sheet.save(os.path.join(a.out, "palette.png"))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
