#!/usr/bin/env python3
"""Cut agent bodies out of their background and normalise them.

Usage:
  python cutout.py --in renders/ --out agent-kit/bodies --mode glass
  python cutout.py --in a.png b.png --out agent-kit/bodies --mode solid

Modes:
  solid   opaque art (clay, matte, flat illustration) on any plain background. A PNG that already has a
          transparent background is used as it is (its alpha wins), so ask the image model for a transparent
          background when the body might share a colour with a plain one.
  glass   glossy or frosted glass on a dark background: the body stays mostly solid, edges and glow stay soft
  marble  clear outer shell around a frosted core, on a dark background: the clear shell becomes see-through

For each image it writes <name>.png (1024px) and <name>@512.png, every body centred on a square canvas, and adds
or updates the agent in agents.json (next to --out's parent) with its ground line ("bottom") measured and default
face settings to tune afterwards. The file name (minus extension) becomes the agent name.
"""
import argparse, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd


def largest(mask):
    lab, n = nd.label(mask)
    if n == 0:
        return mask
    sizes = nd.sum(mask, lab, range(1, n + 1))
    return lab == (int(np.argmax(sizes)) + 1)


def cut(path, mode, work=1536):
    src = Image.open(path)
    src.thumbnail((work, work), Image.LANCZOS)
    rgba = np.asarray(src.convert("RGBA")).astype(np.float32)
    al = rgba[..., 3]
    # Already transparent (e.g. generated with background "transparent"): trust its alpha, don't key by colour.
    # Colour keying fails when the body shares a colour with the background (a cream top on light grey).
    if al.mean() < 250 and np.median(np.concatenate([al[:12, :12].ravel(), al[:12, -12:].ravel(), al[-12:, :12].ravel(), al[-12:, -12:].ravel()])) < 10:
        keep = largest(nd.binary_fill_holes(al > 128))
        near = nd.binary_dilation(keep, iterations=6)
        a = np.where(near, al / 255.0, 0.0)
        return finish(np.dstack([rgba[..., :3], a * 255]).astype(np.uint8), a, "alpha")
    rgb = rgba[..., :3]
    h, w = rgb.shape[:2]
    corners = np.concatenate([rgb[:20, :20].reshape(-1, 3), rgb[:20, -20:].reshape(-1, 3), rgb[-20:, :20].reshape(-1, 3), rgb[-20:, -20:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    dark_bg = bg.max() < 40
    if mode in ("glass", "marble") and not dark_bg:
        print(f"  warning: {os.path.basename(path)} is not on a dark background; glass and marble modes expect black. Using solid.")
        mode = "solid"
    if dark_bg:
        m = rgb.max(2)
    else:
        m = np.abs(rgb - bg).max(2)  # distance from the background colour
    solid = largest(nd.binary_fill_holes(nd.binary_closing(m > (60 if dark_bg else 28), iterations=3)))
    core = nd.binary_erosion(solid, iterations=2)
    a = nd.gaussian_filter(core.astype(np.float32), 1.2)
    band = (nd.distance_transform_edt(~solid) < 30) & ~core
    soft = np.clip((m - 14) / 70, 0, 1) ** 1.4
    a = np.where(band, np.maximum(a, soft), a)
    a = np.where(core, 1.0, a)
    if mode == "glass":
        inner = np.clip((m - 30) / 190, 0.45, 1.0) ** 0.9
        a = np.where(core, inner, a)
    elif mode == "marble":
        inner = np.clip((m - 10) / 175, 0.1, 1.0) ** 0.85
        a = np.where(core, inner, a)
    col = rgb
    if dark_bg:  # un-premultiply so soft edges don't go grey
        col = np.clip(rgb / np.maximum(a, 1e-3)[..., None], 0, 255)
    out = np.dstack([col, a * 255]).astype(np.uint8)
    return finish(out, a, mode)


def finish(out, a, mode):
    """Crop to the body, centre it on a square canvas and measure where it meets the ground."""
    yy, xx = np.where(a > 0.03)
    if yy.size == 0 or (yy.max() - yy.min()) < 8 or (xx.max() - xx.min()) < 8:
        raise ValueError("no body found (the image is blank, too small, or the body matches the background)")
    y0, y1, x0, x1 = yy.min(), yy.max(), xx.min(), xx.max()
    crop = out[y0:y1 + 1, x0:x1 + 1]
    ch, cw = crop.shape[:2]
    side = int(max(ch, cw) * 1.06)
    canvas = np.zeros((side, side, 4), np.uint8)
    oy, ox = (side - ch) // 2, (side - cw) // 2
    canvas[oy:oy + ch, ox:ox + cw] = crop
    bottom = (oy + ch) / side
    return Image.fromarray(canvas.astype(np.uint8)), bottom, cw / ch, mode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inputs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["solid", "glass", "marble"], default="solid")
    args = ap.parse_args()
    files = []
    for p in args.inputs:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        else:
            files.append(p)
    if not files:
        sys.exit("No images found.")
    os.makedirs(args.out, exist_ok=True)
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(args.out)), "agents.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {"agents": {}}
    done, skipped = 0, []
    for f in files:
        # file names become agent names: keep them to safe characters so they work as ids and in JSX
        name = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(f))[0].lower()).strip("-")[:40] or "agent"
        try:
            img, bottom, aspect, used = cut(f, args.mode)
        except Exception as e:  # one bad render must not sink the others
            skipped.append((os.path.basename(f), str(e)))
            print(f"  skipped {os.path.basename(f)}: {e}")
            continue
        img.resize((1024, 1024), Image.LANCZOS).save(os.path.join(args.out, f"{name}.png"), optimize=True)
        img.resize((512, 512), Image.LANCZOS).save(os.path.join(args.out, f"{name}@512.png"), optimize=True)
        entry = cfg["agents"].get(name, {"face": [0.5, 0.55], "dx": 0.15, "w": 0.084, "h": 0.125, "mood": "neutral", "scale": 1})
        entry["bottom"] = round(bottom, 3)
        if aspect > 1.35 and "scale" not in cfg["agents"].get(name, {}):
            entry["scale"] = 1.12  # wide bodies read small; nudge them up
        cfg["agents"][name] = entry
        json.dump(cfg, open(cfg_path, "w"), indent=2)   # saved after every body, so a later failure loses nothing
        done += 1
        print(f"  {name}: mode {used}, aspect {aspect:.2f}, ground at {bottom:.3f}")
    print(f"Wrote {done} bodies to {args.out} and settings to {cfg_path}" + (f"; skipped {len(skipped)}" if skipped else ""))
    if not done:
        sys.exit("No bodies could be cut out. Regenerate the images (see the reasons above).")


if __name__ == "__main__":
    main()
