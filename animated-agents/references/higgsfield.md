# Generating with Higgsfield (when the Higgsfield connector is available)

Check first: if tools such as `generate_image` and `models_explore` from Higgsfield are not available, skip this
file. Give the user the prompts from `brief.md` / `prompts.md` to run themselves and continue once they upload
the renders.

## Credits: always ask first

Every generation spends the user's Higgsfield credits. Before each batch, call the generation tool with
`get_cost: true` in params, tell the user the total ("5 bodies, about N credits"), and wait for a yes.
Never retry a generation automatically after a timeout: the job may already be running.

## Model choice

- Use `models_explore` (`action: "recommend"`, `type: "image"`, `input: "image"`) to confirm current models and
  each model's reference role name; catalogs change.
- **Skip Marketing Studio models** even if they rank first: they're built for ad layouts, not clean character bodies.
- Good defaults (tested October 2026): `gpt_image_2_5` with `quality: "high"`, `resolution: "2k"`,
  `aspect_ratio: "1:1"` (about 2.75 credits per image), or `flux_3_image` (strong with several references).
  Both take references under the role `image_references`.
- For solid materials (clay, flat illustration) `gpt_image_2_5` can return a transparent background directly
  (`background: "transparent"`); still run `cutout.py --mode solid` to normalise. For glass, marble and frosted
  materials keep the flat black background, because the cutout reads the glass against black.
- Concepts: `count: 4` variants of the hero prompt is the cheap way to let the user pick a direction.

## Order of work

1. **Concepts (optional):** 2 to 4 variants of the hero only. The user picks one, or asks for changes.
2. **Hero:** generate the hero body. Show it. Adjust and regenerate until the user approves.
3. **The rest:** for each other agent, pass the approved hero as a reference: in `params.medias`, add
   `{ "value": "<hero job_id>", "role": "image_references" }` (a completed job_id can be used
   directly; check the role name in `models_explore`). Add the "Match the reference image exactly..." line to the
   prompt. Generate them as one batch if the batch tool is available, otherwise one by one.
4. **Review the set together:** consistency of material and colour, distinct silhouettes, no faces, plain background.
   Regenerate any outlier with the same hero reference.

## Bringing the images into the kit

Get each result's image URL (from the generation result, or `show_generations`). Then:

```bash
python scripts/fetch_images.py --out <kit>/renders hero=<url> scout=<url> ...
```

If it reports BLOCKED, the code sandbox can't reach Higgsfield's image host. Give the user the links (named), ask
them to download and upload the images to the chat with those names, and continue from the cutout step. Mention
once that an org admin can allow the image host's domain in Claude's code execution network settings to make this
automatic.

Background removal: our `cutout.py` handles plain backgrounds well and keeps glass translucent. Higgsfield's
`remove_background` is an alternative for busy backgrounds, but it makes glass fully opaque, so prefer `cutout.py`
for glass and marble materials.
