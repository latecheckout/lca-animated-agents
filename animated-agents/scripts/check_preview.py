#!/usr/bin/env python3
"""Screenshot a preview page in every state and save one contact sheet to look at.

Usage:
  python check_preview.py --html agent-kit/preview.html --out agent-kit/check.png [--faces]

Needs Playwright with Chromium (pip install playwright, then: playwright install chromium).
--faces also writes a close-up per agent (check_<name>.png) for tuning eye positions in agents.json.
Look at the result before handing anything over: eyes on the face, nothing clipped, effects visible.
"""
import argparse, asyncio, os, socket, subprocess, sys, time
from PIL import Image, ImageDraw

STATES = [("idle", 900), ("thinking", 1300), ("working", 1500), ("waiting", 1600), ("blocked", 1300), ("done", 450)]


async def run(html, out, faces):
    from playwright.async_api import async_playwright
    folder, name = os.path.dirname(os.path.abspath(html)), os.path.basename(html)
    with socket.socket() as so:   # a free port on localhost, so two checks or another server never clash
        so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=folder, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    if srv.poll() is not None:
        sys.exit(f"Couldn't start a local server on port {port}.")
    shots, errors = [], []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/{name}")
            await pg.wait_for_timeout(800)
            await pg.mouse.move(640, 715)
            for st, ms in STATES:
                await pg.click(f'#state button[data-v="{st}"]')
                await pg.wait_for_timeout(ms)
                path = os.path.join(folder, f".shot_{st}.png")
                await pg.screenshot(path=path, clip={"x": 0, "y": 40, "width": 1280, "height": 390})
                shots.append((st, path))
            if faces:
                await pg.click('#state button[data-v="idle"]')
                await pg.wait_for_timeout(600)
                figs = await pg.query_selector_all("#cast figure")
                for i, f in enumerate(figs):
                    cap = await f.query_selector("figcaption")
                    label = ((await cap.inner_text()) if cap else str(i)).strip().lower().replace(" ", "-")
                    await f.screenshot(path=os.path.join(folder, f"check_{label}.png"))
            await b.close()
    finally:
        srv.kill()
    sheet = Image.new("RGB", (1280, 390 * len(shots)), "white")
    for i, (st, path) in enumerate(shots):
        sheet.paste(Image.open(path), (0, 390 * i))
        ImageDraw.Draw(sheet).text((10, 390 * i + 8), st.upper(), fill=(0, 0, 0))
        os.remove(path)
    sheet.save(out)
    print(f"Saved {out}" + (f"  PAGE ERRORS: {errors}" if errors else "  (no page errors)"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--faces", action="store_true")
    a = ap.parse_args()
    asyncio.run(run(a.html, a.out, a.faces))
