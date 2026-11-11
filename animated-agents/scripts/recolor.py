#!/usr/bin/env python3
"""Recolour cut-out bodies to a new palette without regenerating them.

Usage:
  python recolor.py --in agent-kit/bodies --out agent-kit/bodies-new --palette "#76927A,#A8C2CF,#BCD6E6,#F0E8D2,#FCFAF4"
  [--bottom "#9CB68A" --bottom-amount 0.5]   optional colour that settles along the bottom of each body
  [--saturation 1.0]                         below 1 mutes the result, above 1 makes it richer

The palette runs from the darkest tone to the lightest. Each pixel's brightness picks its colour along it, so the
shading and form survive; near-white highlights stay white and the transparency is untouched. Works on the
<name>.png / <name>@512.png files written by cutout.py.
"""
import argparse, os
import numpy as np
from PIL import Image


def hexrgb(h):
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--palette", required=True)
    ap.add_argument("--bottom")
    ap.add_argument("--bottom-amount", type=float, default=0.5)
    ap.add_argument("--saturation", type=float, default=1.0)
    a = ap.parse_args()
    cols = np.array([hexrgb(c) for c in a.palette.split(",")], np.float32)
    xs = np.linspace(0, 1, len(cols))
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(os.listdir(a.src)):
        if not f.lower().endswith(".png"):
            continue
        img = np.asarray(Image.open(os.path.join(a.src, f)).convert("RGBA")).astype(np.float32)
        rgb, al = img[..., :3], img[..., 3]
        L = (0.30 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]) / 255
        L = np.clip((L - 0.16) / 0.8, 0, 1) ** 0.88
        new = np.stack([np.interp(L, xs, cols[:, c]) for c in range(3)], -1)
        if a.bottom:
            yy = np.where(al > 40)[0]
            y0, y1 = (yy.min(), yy.max()) if len(yy) else (0, al.shape[0] - 1)
            yn = np.clip((np.arange(al.shape[0])[:, None] - y0) / max(y1 - y0, 1), 0, 1)
            band = (np.clip((yn - 0.52) / 0.42, 0, 1) ** 1.1 * a.bottom_amount)
            band = np.broadcast_to(band, L.shape)[..., None]
            tint = np.array(hexrgb(a.bottom), np.float32) * (0.9 + 0.15 * L[..., None])
            new = new * (1 - band) + tint * band
        sat = (rgb.max(2) - rgb.min(2)) / 255
        w = np.clip(0.35 + 1.4 * sat, 0, 1)[..., None]  # keep near-white highlights white
        out = rgb * (1 - w) + new * w
        g = out.mean(2, keepdims=True)
        out = g + (out - g) * a.saturation
        Image.fromarray(np.dstack([out, al]).clip(0, 255).astype(np.uint8)).save(os.path.join(a.out, f), optimize=True)
        print("  recoloured", f)


if __name__ == "__main__":
    main()
