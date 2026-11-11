#!/usr/bin/env python3
"""Build a finished agent kit from generated renders, entirely inside the person's Higgsfield sandbox.

This is the conversation-only route (no studio page): Claude generates the bodies with the Higgsfield connector,
installs this script in the Higgsfield sandbox (see scripts/remote_bundle.py), and runs:

  python3 kit_remote.py --title "Glass helpers" --mode glass agent-1=<render url> agent-2=<render url> ...
  (the labels before = are only for reporting; agents are named after the kit: glass-helpers-1, glass-helpers-2, ...)

--mode is the cutout mode: glass (glass, frosted, jelly, marble bodies on black) or solid (clay, plush, ceramic,
flat; generate those with a transparent background). Names become the agent names in the kit.

It downloads the renders, cuts them out, places the eyes automatically, and writes:
  out/<slug>-kit.zip   bodies, agents.json, live-agent.js (one-file web component), Agent.jsx + agentRig.js
                       (React), preview.html (every state, 48px and 32px rows), README.md
  out/sheet.png        a small contact sheet of the cut-out bodies, for Claude to look at (sandbox image_paths)
A render that can't be downloaded or cut out is skipped and listed under "skipped"; the kit still builds from the rest.
The last stdout line is JSON: {"zip": path, "sheet": path, "agents": {...}, "skipped": [...]}. Upload the zip with media_upload +
a curl PUT in the same command, then media_confirm (type "file") for a permanent download link.
"""
import argparse, base64, io, json, os, re, sys, urllib.request, zipfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cutout import cut  # noqa: E402

STATES = [("idle", "Idle"), ("thinking", "Thinking"), ("working", "Working"), ("waiting", "Waiting"), ("blocked", "Blocked"), ("done", "Done")]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "agents").lower()).strip("-")[:24] or "agents"


def auto_face(im):
    """Same placement as the studio: eyes a little below the middle of the body's bounding box."""
    a = np.asarray(im.resize((128, 128), Image.LANCZOS).convert("RGBA")).astype(np.float32)
    al = a[..., 3]
    ys, xs = np.where(al > 60)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    bw, bh = (x1 - x0) / 128, (y1 - y0) / 128
    solid = al > 200
    rgb = a[..., :3][solid].mean(0) if solid.any() else np.array([120, 170, 255])
    return {"face": [round((x0 + x1) / 2 / 128, 4), round(y0 / 128 + 0.58 * bh, 4)], "dx": round(0.19 * bw, 4),
            "w": round(0.105 * bw, 4), "h": round(min(0.156 * bw, 0.2 * bh), 4), "scale": 1,
            "tint": ",".join(str(int(v)) for v in rgb)}


def png_bytes(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Agents")
    ap.add_argument("--mode", choices=["glass", "marble", "solid"], default="glass")
    ap.add_argument("--out", default="out")
    ap.add_argument("items", nargs="+", help="name=url")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); os.makedirs("renders", exist_ok=True)
    rig = open(os.path.join(HERE, "agentRig.js")).read()
    rig_plain = re.sub(r"^export (function|const) ", r"\1 ", rig, flags=re.M)
    agents, bodies512, files, skipped = {}, {}, {}, []
    kit_slug = re.sub(r"-set$", "", slug(a.title)) or "agents"   # same naming as the studio's export
    for i, it in enumerate(a.items, 1):
        if "=" not in it:
            sys.exit(f"Expected label=https-url, got: {it}")
        label, url = it.split("=", 1)
        # agents are named after the kit (glass-helpers-1, -2, ...) so two kits on one page never collide
        name = f"{kit_slug}-{i}"
        if not url.startswith("https://"):
            skipped.append((label, "only https:// links are allowed")); continue
        path = os.path.join("renders", name + ".png")
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(path, "wb") as f:
                f.write(r.read())
            body, bottom, aspect, used = cut(path, a.mode)
        except Exception as e:  # one bad render must not throw away the good ones
            skipped.append((label, str(e)[:160])); print(f"  skipped {label}: {e}", flush=True); continue
        big = body.resize((1024, 1024), Image.LANCZOS)
        small = body.resize((512, 512), Image.LANCZOS)
        cfg = auto_face(small); cfg["bottom"] = round(bottom, 4)
        if aspect > 1.35: cfg["scale"] = 1.12   # wide bodies read small; nudge them up
        agents[name] = cfg
        files[f"bodies/{name}.png"] = png_bytes(big)
        p512 = png_bytes(small); files[f"bodies/{name}@512.png"] = p512
        bodies512[name] = "data:image/png;base64," + base64.b64encode(p512).decode()
        print(f"  {name}: cut out ({used}), ground {cfg['bottom']}", flush=True)
    if not agents:
        print(json.dumps({"error": "no bodies could be cut out", "skipped": skipped})); sys.exit(1)
    kit = {"agents": agents, "glow": 0}
    first = next(iter(agents))
    files["agents.json"] = json.dumps(kit, indent=2).encode()
    files["agentRig.js"] = (rig_plain + "\nexport { createAgent, defineAgents, setEffectColors, agentNames };\n").encode()
    files["Agent.jsx"] = AGENT_JSX.encode()
    files["live-agent.js"] = web_component(rig_plain, kit, bodies512, first).encode()
    files["preview.html"] = preview_html(a.title, list(agents)).encode()
    files["README.md"] = readme(a.title, list(agents)).encode()
    zpath = os.path.join(a.out, f"{slug(a.title)}-kit.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in files.items():
            z.writestr("agents/" + k, v)
    # contact sheet for Claude to check the cutouts (kept small enough for sandbox image_paths)
    n = len(agents); sheet = Image.new("RGB", (200 * n, 200), (242, 241, 238))
    for i, nm in enumerate(agents):
        t = Image.open(io.BytesIO(files[f"bodies/{nm}@512.png"])).resize((192, 192), Image.LANCZOS)
        sheet.paste(t, (200 * i + 4, 4), t)
    spath = os.path.join(a.out, "sheet.png"); sheet.save(spath, optimize=True)
    print(json.dumps({"zip": os.path.abspath(zpath), "sheet": os.path.abspath(spath), "bytes": os.path.getsize(zpath), "agents": agents, "skipped": skipped}))


AGENT_JSX = """"use client";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { createAgent, defineAgents } from "./agentRig.js";
import kit from "./agents.json";

defineAgents(kit.agents);

/** <Agent name="agent-1" state="thinking" size={96} />  states: idle, thinking, working, waiting, blocked, done, sleeping */
export const Agent = forwardRef(function Agent({ name, state = "idle", size = 64, glow = 0, basePath = "/agents", src, interactive = true, ...rest }, ref) {
  const host = useRef(null), inst = useRef(null);
  useEffect(() => {
    const a = createAgent(host.current, name, src || `${basePath}/${name}${size <= 128 ? "@512" : ""}.png`, { size, interactive, state, glow });
    const t = kit.agents[name]?.tint; if (t) a.setTint({ aura: t, aura2: t });
    inst.current = a; return () => { a.destroy(); inst.current = null; };
  }, [name, size, src, basePath, interactive]);
  useEffect(() => { inst.current?.setState(state); }, [state]);
  useEffect(() => { inst.current?.setGlow(glow); }, [glow]);
  useImperativeHandle(ref, () => ({ bounce: () => inst.current?.bounce() }), []);
  return <div ref={host} {...rest} />;
});
export default Agent;
"""


def web_component(rig, kit, bodies, first):
    return f"""/* live-agent.js: drop-in animated agents. No build step, no dependencies.
   <script src="live-agent.js"></script>
   <live-agent name="{first}" state="idle" size="96"></live-agent>
   Attributes: name, state (idle | thinking | working | waiting | blocked | done | sleeping), size (px), glow (0-2). */
(function () {{
{rig}
const KIT = {json.dumps(kit)};
const BODIES = {json.dumps(bodies)};
defineAgents(KIT.agents);
// Every kit loaded on the page registers its agents in one shared registry, so a single <live-agent> element
// serves all of them, whichever kit's script happened to load first.
const REG = window.LiveAgents = window.LiveAgents || {{ names: [], kits: {{}} }};
for (const n in BODIES) {{ REG.kits[n] = {{ body: BODIES[n], tint: KIT.agents[n] && KIT.agents[n].tint, create: createAgent }}; if (REG.names.indexOf(n) < 0) REG.names.push(n); }}
class LiveAgent extends HTMLElement {{
  static get observedAttributes() {{ return ["name", "state", "size", "glow"]; }}
  connectedCallback() {{ this.style.display = this.style.display || "inline-block"; this.mount(); }}
  disconnectedCallback() {{ if (this.a) {{ this.a.destroy(); this.a = null; }} }}
  attributeChangedCallback(k) {{ if (!this.isConnected) return; if (k === "state" && this.a) this.a.setState(this.getAttribute("state") || "idle"); else if (k === "glow" && this.a) this.a.setGlow(+this.getAttribute("glow") || 0); else this.mount(); }}
  mount() {{ this.disconnectedCallback(); const n = this.getAttribute("name"), k = window.LiveAgents.kits[n]; if (!k) return;
    this.a = k.create(this, n, k.body, {{ size: +this.getAttribute("size") || 64, state: this.getAttribute("state") || "idle", glow: +this.getAttribute("glow") || 0, interactive: this.getAttribute("interactive") !== "false" }});
    if (k.tint) this.a.setTint({{ aura: k.tint, aura2: k.tint }}); }}
  bounce() {{ if (this.a) this.a.bounce(); }}
}}
if (!customElements.get("live-agent")) customElements.define("live-agent", LiveAgent);
// tags already on the page that were waiting for this kit's agents
document.querySelectorAll("live-agent").forEach(function (el) {{ if (!el.a && el.isConnected && el.mount) el.mount(); }});
}})();
"""


def preview_html(title, ids):
    t = title.replace("<", "")
    big = "".join(f'<live-agent name="{i}" size="160"></live-agent>' for i in ids)
    row = lambda px: "".join(f'<live-agent name="{i}" size="{px}" interactive="false"></live-agent>' for i in ids)
    def opts(name, items, on):
        b = "".join(f'<button data-v="{v}" aria-pressed="{str(v == on).lower()}">{l}</button>' for v, l in items)
        return f'<div class="ctrl"><span class="label">{name}</span><div class="opts" data-k="{name.lower()}">{b}</div></div>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title>
<style>:root{{--paper:#F2F1EE;--ink:#121211;--muted:#66655F;--rule:#D3D1CB}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Helvetica Neue",Helvetica,Arial,sans-serif;padding:0 24px 40px}}
.wrap{{max-width:1100px;margin:0 auto}}header{{padding:24px 0 18px;border-bottom:2px solid var(--ink);display:flex;justify-content:space-between;align-items:flex-end}}
h1{{font-weight:400;font-size:28px;letter-spacing:-.02em;margin:0}}.label{{font:11.5px ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
.stage{{background:#E9E7E2;margin-top:20px;min-height:340px;display:flex;align-items:center;justify-content:center;gap:40px;flex-wrap:wrap;padding:40px;transition:background .3s}}
body.dark .stage{{background:#161615}}
.ctrls{{display:flex;flex-wrap:wrap;gap:0 56px;border-bottom:1px solid var(--rule)}}.ctrl{{display:flex;flex-direction:column;gap:10px;padding:16px 0}}
.opts{{display:flex;flex-wrap:nowrap}}.opts button{{white-space:nowrap;height:32px;padding:0 12px;border:1px solid var(--rule);background:transparent;margin:0 -1px -1px 0;font:13px inherit;color:var(--muted);cursor:pointer}}
.opts button[aria-pressed="true"]{{background:var(--ink);color:var(--paper);border-color:var(--ink);position:relative}}
.sizes{{display:flex;flex-direction:column;gap:14px;padding:18px 0;border-bottom:1px solid var(--rule)}}.sizes div{{display:flex;align-items:flex-end;gap:18px}}.sizes .label{{width:44px}}</style></head>
<body><div class="wrap"><header><h1>{t}</h1><span class="label">{len(ids)} agent{"s" if len(ids) > 1 else ""}</span></header>
<div class="stage">{big}</div>
<div class="ctrls">{opts("State", STATES, "idle")}{opts("Glow", [("0", "Off"), ("1", "On"), ("1.8", "Strong")], "0")}{opts("Surface", [("light", "Light"), ("dark", "Dark")], "light")}</div>
<div class="sizes"><div><span class="label">48px</span>{row(48)}</div><div><span class="label">32px</span>{row(32)}</div></div></div>
<script src="live-agent.js"></script>
<script>document.querySelectorAll(".opts").forEach(function(g){{g.onclick=function(e){{var v=e.target.dataset.v;if(v==null)return;g.querySelectorAll("button").forEach(function(b){{b.setAttribute("aria-pressed",b===e.target)}});var k=g.dataset.k;
if(k==="surface")document.body.classList.toggle("dark",v==="dark");else document.querySelectorAll("live-agent").forEach(function(a){{a.setAttribute(k,v)}});}};}});</script>
</body></html>"""


def readme(title, ids):
    tmpl = open(os.path.join(HERE, "README.kit.md")).read() if os.path.exists(os.path.join(HERE, "README.kit.md")) else README_KIT
    return (tmpl.replace("{TITLE}", title).replace("{LIST}", "\n".join(f"- `{i}`" for i in ids))
            .replace("{FIRST}", ids[0]).replace("{NAMES}", ", ".join(f"`{i}`" for i in ids)).replace("{{", "{").replace("}}", "}"))


README_KIT = r'''# {TITLE}

Live animated agents for any prototype. Each agent is a PNG body with eyes and motion drawn in code: no video, no
3D engine, no dependencies.

Agents in this kit:
{LIST}

Open `preview.html` to see every agent in every state, on light and dark, at full size and at 48px and 32px.

## What's inside

| File | Use it for |
| --- | --- |
| `live-agent.js` | Everything in one file (engine + bodies). Drop it into any page, prototype or no-code tool. |
| `preview.html` | A ready demo of every state and size. Open it in a browser. |
| `Agent.jsx`, `agentRig.js`, `agents.json` | React / Next.js component, the engine as a module, and each agent's eye settings. |
| `bodies/*.png` | The cut-out bodies (512px, transparent), for React or your own use. |

## 1. Any page or prototype (fastest)

```html
<script src="live-agent.js"></script>
<live-agent name="{FIRST}" state="idle" size="96"></live-agent>
```

| Attribute | Values |
| --- | --- |
| `name` | {NAMES} |
| `state` | `idle` (default), `thinking`, `working`, `waiting`, `blocked`, `done`, `sleeping` |
| `size` | pixels, e.g. `32`, `48`, `96`, `160` (default 64). Looks crisp up to about 256px. |
| `glow` | `0` (off, default) to `2`, a soft halo in the agent's own colour |
| `interactive` | `false` to stop the eyes following the pointer and click-to-hop |

Drive it from your code:

```js
const agent = document.querySelector("live-agent");
agent.setAttribute("state", "thinking");   // when your AI starts working
agent.setAttribute("state", "done");       // when it finishes
agent.bounce();                            // a one-off happy hop
```

## 2. No-code tools (Framer, Webflow, Squarespace, Notion sites…)

Upload `live-agent.js` as an asset (or paste its contents into a custom-code / embed block inside `<script>…</script>`),
then use the `<live-agent>` tag in an HTML embed. Framer: add it via Site Settings → Custom Code, then an Embed with
the tag. It is a standard web component, so it also works as-is in Vue, Svelte, Angular and plain HTML.

## 3. React / Next.js

1. Copy `Agent.jsx`, `agentRig.js` and `agents.json` into your app, e.g. `src/components/agents/`.
2. Copy `bodies/*.png` into your public folder at `/agents/` (or pass `basePath`).
3. Use it:

```jsx
import {{ Agent }} from "./components/agents/Agent.jsx";

<Agent name="{FIRST}" state={{isBusy ? "working" : "idle"}} size={{64}} />
```

Props: `name`, `state`, `size`, `glow`, `interactive`, `basePath`, `src`. `ref.current.bounce()` gives a hop.
It is marked `"use client"` for the Next.js app router. Your bundler needs JSON imports (Vite, Next.js and CRA do).

Prefer the web component in React? Load `live-agent.js` once and use `<live-agent name="{FIRST}" state="idle" />`.
In TypeScript, declare the tag once:

```ts
declare namespace JSX {{ interface IntrinsicElements {{ "live-agent": any }} }}
```

## Adjusting

Each agent's eyes live in `agents.json`: `face` is the centre point between the eyes and `dx` half the gap between
them (both as fractions of the body image), `w` and `h` the eye size, `bottom` where the body meets the ground.
Change a number, reload. Motion respects the viewer's reduced-motion setting automatically.
'''


if __name__ == "__main__":
    main()
