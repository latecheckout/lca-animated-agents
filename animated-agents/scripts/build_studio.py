#!/usr/bin/env python3
"""Build the Agent Studio page: inline the animation engine and the cutout script into assets/studio/studio.src.html.

Usage:
  python build_studio.py [--server Higgsfield] [--out assets/studio/studio.html]

--server is the display name of the viewer's Higgsfield connector (the one with generate_image and sandbox_exec).
The result is one self-contained page to publish as an Artifact (see SKILL.md, "The studio").
"""
import argparse, base64, hashlib, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="Higgsfield")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "studio", "studio.html"))
    a = ap.parse_args()
    src = open(os.path.join(ROOT, "assets", "studio", "studio.src.html")).read()
    rig = open(os.path.join(ROOT, "assets", "template", "agentRig.js")).read()
    rig = re.sub(r"^export (function|const) ", r"\1 ", rig, flags=re.M)
    rig = rig.replace("</script", "<\\/script")
    cut_src = open(os.path.join(HERE, "cutout.py"), "rb").read()
    cut = base64.b64encode(cut_src).decode()
    src = src.replace("__CUTOUT_VER__", hashlib.sha1(cut_src).hexdigest()[:10])
    # example agents for the opening screen: assets/studio/examples/agent-N-512.png, ground line and eye height per body
    ex_meta = [("agent-1", 0.972, 0.55), ("agent-2", 0.972, 0.52), ("agent-3", 0.970, 0.66)]
    ex = [{"id": "ex-" + n, "bottom": b, "eyeY": y, "body": "data:image/png;base64," + base64.b64encode(open(os.path.join(ROOT, "assets", "studio", "examples", n + "-512.png"), "rb").read()).decode()} for n, b, y in ex_meta]
    logo = "data:image/png;base64," + base64.b64encode(open(os.path.join(ROOT, "assets", "studio", "lca-logo.png"), "rb").read()).decode()
    sw = {n: "data:image/png;base64," + base64.b64encode(open(os.path.join(ROOT, "assets", "studio", "swatches", n + ".png"), "rb").read()).decode()
          for n in ("auto", "glass", "frosted", "jelly", "clay", "plush", "ceramic", "flat")}
    src = src.replace("__SWATCHES__", json.dumps(sw))
    # ready-made sets: assets/studio/ready/sets.json + one 512px body per agent
    rdir = os.path.join(ROOT, "assets", "studio", "ready")
    sets = json.load(open(os.path.join(rdir, "sets.json")))
    for key, st in sets.items():
        for it in st["items"]:
            it["body"] = "data:image/png;base64," + base64.b64encode(open(os.path.join(rdir, key, it["id"] + "-512.png"), "rb").read()).decode()
    src = src.replace("__READY_SETS__", json.dumps(sets))
    out = src.replace("__LOGO__", logo).replace("__EXAMPLES__", json.dumps(ex)).replace("/*__RIG__*/", rig).replace("__CUTOUT_B64__", cut).replace('"__HF_SERVER__"', json.dumps(a.server).replace("</", "<\\/"))
    for tok in ("/*__RIG__*/", "__CUTOUT_B64__", "__HF_SERVER__", "__EXAMPLES__", "__LOGO__", "__SWATCHES__", "__READY_SETS__"):
        assert tok not in out, tok
    open(a.out, "w").write(out)
    print(f"Wrote {a.out} ({len(out) // 1024} KB, connector: {a.server})")

if __name__ == "__main__":
    main()
