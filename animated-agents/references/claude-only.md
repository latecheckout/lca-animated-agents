# The Claude-only route (no studio page)

For people who want to do it all in conversation, or whose Claude can't publish the studio. Everything heavy runs in
their own Higgsfield sandbox (it has Python, Pillow, NumPy, SciPy and internet), so nothing has to be downloaded into
Claude's own environment, which often can't reach Higgsfield's image host. Tested end to end on 2026-11-04.

## 1. Plan and generate (connector tools)

- Agree the brief and cast as in `brief.md` (or straight from a one-line idea). 1 to 5 agents. No names needed:
  call them agent-1, agent-2, ...
- Build each prompt from `prompts.md`. Glass, frosted, jelly and marble bodies go on a flat pure black background.
  Solid bodies (clay, plush, ceramic, flat) are generated with `background: "transparent"` so the cutout never
  keys by colour.
- Check the cost first (`generate_image` with `get_cost: true`; about 1.5 credits per image at quality high, 1k),
  say it, and wait for a yes.
- `generate_image_batch` with model `gpt_image_2_5`, `quality: "high"`, `resolution: "1k"`, `aspect_ratio: "1:1"`.
  Do agent-1 alone first; once it's done, show it and generate the rest with
  `medias: [{value: <agent-1 job_id>, role: "image_references"}]` and the "Match the reference image exactly..." line.
- Poll with `jobs_wait` (15 s at a time) until each job is `completed`; take each job's `result_url`.

## 2. Build the kit in the Higgsfield sandbox (one `sandbox_exec`)

```bash
mkdir -p ~/agent-kit && cd ~/agent-kit \
 && curl -sfL -o bundle.zip 'BUNDLE_URL' \
 && python3 -c "import hashlib,sys; sys.exit(hashlib.sha256(open('bundle.zip','rb').read()).hexdigest() != 'BUNDLE_SHA256')" \
 && unzip -oq bundle.zip \
 && python3 kit_remote.py --title "<set name>" --mode <glass|solid> agent-1=<url> agent-2=<url> agent-3=<url>
```

`BUNDLE_URL` and `BUNDLE_SHA256` are the hosted bundle and its checksum (below). If the checksum line fails, stop:
don't unzip it, use the install command at the end of "The bundle" instead. Pass `image_paths: ["agent-kit/out/sheet.png"]` in the same call so the
cut-out bodies come back as an image: look at it. If one is clipped or messy, regenerate that agent and rerun.
Agents in the kit are named after the title (`glass-helpers-1`, `-2`, ...) so two kits never collide. A render that
can't be cut out is skipped and listed under `skipped` in the last stdout line (JSON); the kit builds from the rest,
so regenerate only the skipped one.

## 3. Hand the kit over (a permanent download link)

1. `media_upload` with `filename: "<set-name>-kit.zip"` gives an `upload_url` and a permanent `url`.
2. One `sandbox_exec`:
   `cd ~/agent-kit && curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: application/octet-stream" -H "If-None-Match: *" --data-binary @out/<set-name>-kit.zip '<upload_url>'`
   (the `If-None-Match: *` header is required by the signed link; expect 200).
3. `media_confirm` with `type: "file"` and the `media_id`.
4. Give the person the `url`. Inside the zip: `preview.html` (every state, light/dark, glow, 48px and 32px rows),
   `live-agent.js` (one-file web component: `<script src="live-agent.js"></script><live-agent name="<set-name>-1" state="thinking">`),
   `Agent.jsx` + `agentRig.js` + `agents.json` for React, the body PNGs, and a README.

## The bundle

`scripts/remote_bundle.py --zip agent-kit-bundle.zip` packs `cutout.py`, `kit_remote.py` and `assets/template/agentRig.js`.
The hosted copy is `bundle/agent-kit-bundle.zip` in the skill's GitHub repo:

BUNDLE_URL = https://raw.githubusercontent.com/latecheckout/lca-animated-agents/main/bundle/agent-kit-bundle.zip
BUNDLE_SHA256 = fc85f215fa97e1423aad52fe98c1f2fcb1e60aa761d1e72135d13d3a12e9876d

After changing any of those three files, rebuild the zip, commit it and update the checksum. If the URL ever fails, `python remote_bundle.py --out install.txt`
writes a self-contained install command (about 23 KB) to run in the sandbox instead.

## Tuning afterwards

Eye position per agent is in `agents.json` inside the kit. To change it, edit the values (`face`, `dx`, `w`, `h`) and
rebuild, or open the studio page for sliders. `eyeStyle` picks the look: `"classic"` (the default pill eyes), `"kawaii"`
(big round eyes with a white rim, a shine and a tiny "w" mouth) or `"smiley"` (dot eyes and a wide smile). Kawaii and
Smiley mouths change with the state on their own.
