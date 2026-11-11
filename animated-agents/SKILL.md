---
name: "animated-agents"
description: Design and animate AI agent mascots, from a one-line idea, a moodboard, inspiration images or existing character images, as live code-animated agents with blinking eyes, hops and work states (idle, thinking, working, waiting, blocked, done), exported as a kit for any prototype (web component, React, PNGs). Use it whenever someone wants mascots, agent characters, agent avatars or assistant characters, wants to animate mascots, asks for "living" agents like Grok Bot's, uploads character images and says something like "animate these", or asks to "surprise me" or "roll the dice". With the Higgsfield connector it opens the Agent Studio, a page where the person describes agents, generates them on their own Higgsfield account, tunes them and exports the kit; it can also do everything in chat. Without Higgsfield it offers ready-made sets or writes the image prompts. Also use it to recolour a set, tune the eyes or change how a state moves.
---

# Animated agents

Takes a moodboard (or finished character images) all the way to live agents: it can design the cast and write or
generate the art, then animate it. Each body is a PNG, the eyes are drawn in code on top so they
can blink, look around and change with the state, and all the motion runs in a small JavaScript engine. No video:
it is light, instant to change, and drops straight into a prototype.

The people using this skill are both designers (care about the look, the motion and the prompts) and developers
(care about the component and the API). Explain in plain language; keep technical detail for the README.

## Start here: the studio

The default way to run this skill is the **Agent Studio**, an LCA Labs page the person uses themselves, in three
steps: connect Higgsfield; describe the agents (text and/or inspiration images, a material, 1 to 5 agents, or
Randomize) and generate; then the agents arrive already animated, with every state, glow, light/dark, 48px and 32px
previews, eye tuning, Regenerate per agent (edit the shape or keep it), and Export kit. Everything runs on their account and credits.
2D only: glossy materials (glass, frosted, jelly) give the 3D look. No Higgsfield account? The page offers three ready-made
sets (flat, glass, plush; three agents each) with every state and a full export, so anyone gets usable assets. People can also skip the page and run the skill
conversationally (the workflow further down); both should keep working.

1. Check that this conversation has the Higgsfield connector (tools such as `generate_image` and `sandbox_exec`).
   If not, tell them to add Higgsfield in claude.ai under Settings → Connectors and come back. Note the connector's
   exact display name (usually "Higgsfield"; if they have more than one, use the one with `sandbox_exec`).
2. If the name isn't "Higgsfield", rebuild the page for it: `python scripts/build_studio.py --server "<name>"`.
   Otherwise use `assets/studio/studio.html` as it is (it's prebuilt).
3. Publish that file as an Artifact with exactly these capabilities, using their connector name:
   `{"mcp": {"servers": [{"server": "Higgsfield", "tools": ["balance", "generate_image", "generate_image_batch",
   "jobs_wait", "sandbox_exec"]}]}, "sample": {"images": true}, "downloads": true}`
4. Give them the link and one line on using it: the page walks them through Connect → Describe → Agents, shows the
   credit cost on every button that spends, and Export kit saves a zip.
5. If something fails, a "Copy activity log" link appears at the bottom of the page. Ask them to click it and paste
   the result here; it shows which call failed and what Higgsfield said.

How it works, for troubleshooting: Claude (the page's `sample` capability) plans the cast and writes the prompts;
Higgsfield renders the bodies (hero first, the rest use it as a reference); the cutout (`scripts/cutout.py`, inlined)
runs in the person's Higgsfield sandbox because artifact pages can't fetch outside images; the eyes and motion are
`assets/template/agentRig.js`, inlined. The export holds `live-agent.js` (a one-file web component with the bodies
built in), a React component, `agents.json`, the bodies, `preview.html` and a README.

If this Claude can't publish artifacts with connector access, or the person would rather stay in the conversation,
use **the Claude-only route**: read `references/claude-only.md`. It generates with the Higgsfield connector, builds
the whole kit inside their Higgsfield sandbox (cutout, eyes, preview, web component, React files) and hands back a
permanent download link. Nothing needs downloading into Claude's own environment.
After editing the page's source (`assets/studio/studio.src.html`), the engine or `cutout.py`, run
`python scripts/build_studio.py` to rebuild `studio.html`.

## What you deliver

1. **A preview page** (`preview.html`): one self-contained file showing every agent in every state, at large and
   small sizes, with light and dark surfaces. Designers review it; anyone can open it offline or host it.
2. **A developer kit** (`<name>.zip`): `Agent.jsx` (React), `agentRig.js` (the engine, framework-free),
   `agents.json` (per-agent face settings), `bodies/`, `Example.jsx`, `README.md`, the preview.
## Workflow (local, when working in a codebase with Python on the machine)

First time on this machine? Run `python scripts/check_setup.py`; it lists anything missing with the exact
install command.

There are three ways in. Pick based on what the user brings:

- **A one-line idea** → write a short brief from it and start at step A (design the cast), then continue at step 1.
- **A moodboard or a brand** → start at step A (design the cast), then continue at step 1.
- **Finished character images** → skip to step 1.

Set up a working folder (the "kit") for everything: `<kit>/brief`, `<kit>/renders`, `<kit>/bodies`.

### A. Design the cast from a moodboard

Read `references/brief.md` first; it has the full method. In short:

1. **Style brief.** Run `python scripts/moodboard.py --in <moodboard images> --out <kit>/brief`, and look at the
   images yourself too: the script only reads colour. Show `palette.png` and a short brief: material, body
   colours, subject motifs (what the board shows that can live in a body's shape or surface),
   surface, mood words. Confirm it.
2. **Cast.** Agree on how many agents, their names and roles, and a clearly different silhouette for each.
   Choose one simple, balanced "hero" to generate first. Confirm the cast.
3. **Prompts.** Build each from `references/prompts.md` (body only, no eyes or props, plain background).
4. **Generate.**
   - If the Higgsfield connector is available, read `references/higgsfield.md` and follow it: check costs and get
     a yes before each batch, generate (optionally concepts first) the hero, get approval, then generate the rest
     with the hero as the reference image so the set stays consistent. Bring the images into `<kit>/renders` with
     `scripts/fetch_images.py`; if that's blocked, ask the user to download and upload them (named by agent).
   - Without Higgsfield, give the user the prompts (hero first, then the others with the hero attached as a
     reference image in their tool of choice) and wait for the renders.

Keep the user in the loop at three points: the brief, the cast, and the hero. Those are the decisions that matter;
everything after can run without stopping.

### 1. Get the right body images

The best input is **one image per agent: the body only, with no eyes, mouth or props**, front-facing, centred, on a
flat plain background, all with the same lighting and style. The eyes are added in code, so baked-in eyes would
double up and can't animate.

- If the user has no images yet, go back to step A.
- If their images already have faces, ask for versions without them. As a last resort, cut out with `--mode solid`
  and skip the code eyes by setting `w` and `h` to 0 in `agents.json`; the body still moves.
- File names become agent names (`scout.png` → `scout`), so ask for sensible ones.

### 2. Cut out the bodies

```bash
python scripts/cutout.py --in <kit>/renders --out <kit>/bodies --mode <solid|glass|marble>
```

- `solid`: opaque art (matte, clay, flat illustration), any plain background colour.
- `glass`: glossy or frosted glass on black; keeps soft glowing edges, the body mostly solid.
- `marble`: a clear shell around a frosted core, on black; the clear shell becomes see-through.

It writes 1024px and 512px PNGs and creates `<kit>/agents.json` with each agent's ground line measured.
Check the cutouts over a light and a dark background before going on (a quick composite with PIL is enough).

Optional: to match a product palette without regenerating, run `scripts/recolor.py` (dark-to-light palette,
optional colour settling along the bottom). See its docstring.

### 3. Place the eyes

Build the preview, screenshot it, and tune each agent's face in `agents.json` until the eyes sit where a face
would be on that shape. Read `references/tuning.md` for what each setting does and typical values per shape.

```bash
python scripts/build_preview.py --kit <kit> --out <kit>/preview.html --title "<Project> agents"
python scripts/check_preview.py --html <kit>/preview.html --out <kit>/check.png --faces
```

Look at the close-ups (`check_<name>.png`) and adjust. Two or three rounds is normal. Eyes usually sit a little
below the middle of the shape; on tall shapes (flames, triangles) lower; on wide shapes (clouds) smaller.

### 4. Check every state

Look at `check.png` (one row per state). Confirm: eyes on the face in every state, nothing clipped, the
badges visible in blocked ("!") and thinking (dots), and the turn in done keeping the eyes on the body. Read `references/states.md`
when the user wants to change how a state looks or moves; it explains every state and where its settings live.

### 5. Package and hand over

```bash
python scripts/package_kit.py --kit <kit> --out <outputs folder> --name <kit-name>
```

Present the preview page and the zip. In a sentence or two: what's in it, how a developer starts
(`<Agent name="..." state="working" />`), and that eye positions and colours are one-line changes in
`agents.json`. If the conversation has an artifact publishing tool, publish `preview.html` so it has a link.

## Requirements

- Python 3.9+ with Pillow, NumPy and SciPy (cutout, recolour, preview build). `scripts/check_setup.py` checks all
  of this and prints the install commands.
- Node for `npx esbuild` (preview build bundles the engine).
- Playwright with Chromium for `check_preview.py`. If it isn't available, still build the preview and say the
  visual check was skipped.
- Optional: the Higgsfield connector, to generate the character art inside the conversation (uses the user's
  Higgsfield credits). Without it, the skill writes prompts and the user brings the renders.
- For people outside the team: a Higgsfield account connected to Claude, plus the setup check above, is all
  they need. `check_setup.py` needs only Python.

## Things that go wrong

- **Eyes look pasted on or off-centre:** tune `face`, `dx`, `w`, `h` (step 3). Never skip the close-ups.
- **Body sits too high or sinks:** `bottom` is measured automatically; nudge it by 0.01 to 0.02 if needed.
- **Grey halos around glass:** the source wasn't on pure black, or `solid` mode was used on glass. Re-cut.
- **A wide agent looks small next to the others:** raise its `scale` (1.1 to 1.2).
- **A generated set looks inconsistent:** regenerate the outliers with the approved hero as the reference image,
  and repeat the "match the reference exactly" line at the start of the prompt.
- **Downloading generated images is blocked:** expected in some workspaces. Ask for the files, named by agent.
- **The user wants 3D:** this skill is 2D on purpose; glossy materials (glass, frosted, jelly) give the 3D look.
- **A themed agent comes out with a face or props** (a carved pumpkin face, a hat): repeat "completely blank with
  no eyes, no mouth, no face" and move the theme into shape and surface words only.
