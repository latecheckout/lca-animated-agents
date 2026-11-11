#!/usr/bin/env python3
"""Build a single self-contained preview page of every agent in every state.

Usage:
  python build_preview.py --kit agent-kit --out agent-kit/preview.html [--title "Agents"] [--background bg.jpg]

--kit is the folder holding bodies/ and agents.json (from cutout.py). The page embeds the 512px bodies and the
engine, so it opens in any browser with no internet and can be emailed or dropped on Netlify or Vercel as is.
Needs Node (npx esbuild) to bundle the engine.
"""
import argparse, base64, html as html_lib, json, os, re, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.join(HERE, "..", "assets", "template", "agentRig.js")

MAIN = r"""
import { createAgent, defineAgents, setEffectColors } from "__RIG__";
const K = window.AGENT_KIT; defineAgents(K.agents); if (K.effectColors) setEffectColors(K.effectColors);
const names = Object.keys(K.agents), all = [];
const cast = document.getElementById("cast");
for (const n of names) { const f = document.createElement("figure"), h = document.createElement("div"), c = document.createElement("figcaption");
  c.textContent = n.replace(/[-_]/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()); f.append(h, c); cast.append(f);
  all.push(createAgent(h, n, K.bodies[n], { size: 160 })); }
for (const s of [48, 32]) { const row = document.getElementById("s" + s);
  for (const n of names) { const h = document.createElement("div"); row.insertBefore(h, row.lastElementChild); all.push(createAgent(h, n, K.bodies[n], { size: s, interactive: false })); } }
const seg = (id, fn) => { const g = document.getElementById(id); g.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return;
  g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b)); fn(b.dataset.v); }); };
seg("state", (v) => all.forEach((a) => a.setState(v)));
seg("surface", (v) => (document.documentElement.dataset.surface = v));
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>__TITLE__</title>
<style>
:root{--page:#EEF0F4;--ink:#16203A;--muted:#5C6478;--chip:rgba(255,255,255,.72);--line:rgba(22,32,58,.1);--on:#16203A;--onInk:#F4F6FA;color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--page:#EEF0F4}}
:root[data-theme="dark"]{--page:#EEF0F4}
:root[data-surface="dark"]{--page:#0E1220;--ink:#E8ECF6;--muted:#9AA3B8;--chip:rgba(255,255,255,.08);--line:rgba(255,255,255,.12);--on:#E8ECF6;--onInk:#0E1220}
html,body{margin:0;min-height:100%}
body{background:var(--page) __BG__;color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
header{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;justify-content:space-between;padding:22px clamp(16px,4vw,48px)}
h1{font-size:21px;font-weight:600;margin:0}
.ctl{display:flex;flex-wrap:wrap;gap:8px}
.seg{display:flex;flex-wrap:wrap;gap:2px;padding:4px;border-radius:999px;background:var(--chip);border:1px solid var(--line)}
.seg button{font:inherit;font-size:13px;border:0;background:transparent;color:var(--ink);padding:6px 12px;border-radius:999px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--on);color:var(--onInk)}
.seg button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
main{max-width:1180px;margin:0 auto;padding:6vh 16px 56px}
#cast{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:26px 10px;justify-items:center;align-items:end}
figure{margin:0;display:flex;flex-direction:column;align-items:center;gap:14px}
figcaption{font-size:15px;font-weight:600}
.hint{text-align:center;color:var(--muted);font-size:13px;margin:30px 0 0}
.small{margin:38px auto 0;width:max-content;max-width:100%;display:grid;gap:16px;padding:20px 28px;border-radius:24px;border:1px solid var(--line);background:var(--chip)}
.row{display:flex;gap:16px;align-items:end;flex-wrap:wrap}
.row span{font-size:12px;color:var(--muted)}
</style></head><body>
<header><h1>__TITLE__</h1><div class="ctl">
<div class="seg" id="state" role="group" aria-label="State"><button data-v="idle" aria-pressed="true">Idle</button><button data-v="thinking" aria-pressed="false">Thinking</button><button data-v="working" aria-pressed="false">Working</button><button data-v="waiting" aria-pressed="false">Waiting</button><button data-v="blocked" aria-pressed="false">Blocked</button><button data-v="done" aria-pressed="false">Done</button></div>
<div class="seg" id="surface" role="group" aria-label="Surface"><button data-v="light" aria-pressed="true">Light</button><button data-v="dark" aria-pressed="false">Dark</button></div>
</div></header>
<main><div id="cast"></div>
<p class="hint">They follow your pointer when it's near. Click one to make it hop.</p>
<div class="small"><div class="row" id="s48"><span>48px</span></div><div class="row" id="s32"><span>32px</span></div></div></main>
<script>window.AGENT_KIT=__KIT__;</script>
<script>__JS__</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Agents")
    ap.add_argument("--background")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(a.kit, "agents.json")))
    bodies = {}
    for n in cfg["agents"]:
        p = os.path.join(a.kit, "bodies", f"{n}@512.png")
        bodies[n] = "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
    kit = {"agents": cfg["agents"], "effectColors": cfg.get("effectColors"), "bodies": bodies}
    with tempfile.TemporaryDirectory() as td:
        entry = os.path.join(td, "main.js")
        open(entry, "w").write(MAIN.replace("__RIG__", os.path.abspath(RIG).replace("\\", "/")))
        out_js = os.path.join(td, "out.js")
        subprocess.run(["npx", "--yes", "esbuild@0.23.1", entry, "--bundle", "--minify", "--format=iife", "--outfile=" + out_js, "--log-level=warning"], check=True)
        js = open(out_js).read().replace("</script", "<\\/script")
    bg = ""
    if a.background:
        ext = os.path.splitext(a.background)[1].lower().lstrip(".").replace("jpg", "jpeg")
        bg = "url(data:image/%s;base64,%s) center/cover fixed" % (ext, base64.b64encode(open(a.background, "rb").read()).decode())
    # Fill every placeholder in one pass: values can't inject markup (the title is escaped) or another placeholder
    vals = {"__TITLE__": html_lib.escape(a.title), "__BG__": bg, "__KIT__": json.dumps(kit).replace("</", "<\\/"), "__JS__": js}
    html = re.sub("__TITLE__|__BG__|__KIT__|__JS__", lambda m: vals[m.group(0)], PAGE)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w").write(html)
    print(f"Wrote {a.out} ({len(html) // 1024} KB, {len(bodies)} agents)")


if __name__ == "__main__":
    main()
