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
 && curl -sfL -o bundle.zip 'BUNDLE_URL' && unzip -oq bundle.zip \
 && python3 kit_remote.py --title "<set name>" --mode <glass|solid> agent-1=<url> agent-2=<url> agent-3=<url>
```

`BUNDLE_URL` is the hosted bundle (below). Pass `image_paths: ["agent-kit/out/sheet.png"]` in the same call so the
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
Current hosted copy (Higgsfield storage, uploaded 2026-11-04):

BUNDLE_URL = https://d2ol7oe51mr4n9.cloudfront.net/user_38o6K5pe6MGL8oJwU2qdmBPjEIU/37e47250-40e3-4c86-a739-a6e73c79c815.zip

After changing any of those three files, rebuild the zip, host it again and update this URL (a public GitHub repo or
the LCA Labs site is the better long-term home). If the URL ever fails, `python remote_bundle.py --out install.txt`
writes a self-contained install command (about 23 KB) to run in the sandbox instead.

## Tuning afterwards

Eye position per agent is in `agents.json` inside the kit. To change it, edit the values (`face`, `dx`, `w`, `h`) and
rebuild, or open the studio page for sliders.
