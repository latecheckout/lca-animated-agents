# From moodboard to a cast of agents

## 1. The style brief (confirm with the user before generating anything)

Run `scripts/moodboard.py`, show `palette.png`, and write a short brief in plain language:

- **Material:** what the bodies are made of. Pick one from `prompts.md` (slightly frosted glass with shine, frosted
  glass, marble in glass, matte clay, flat illustration) or describe a new one in the same style.
- **Colour:** the body gradient from `palette.json` (top, middle, bottom), turned into the prompt's colour sentence.
- **Surface:** the light or dark background the agents will live on (`background` in `palette.json`, or the
  product's own background if the user has one; use it in the preview with `--background`).
- **Subject and motifs:** look at the images yourself; colour is only half of a moodboard. Name what they
  show (plants, food, weather, objects, other characters) and pick one or two motifs that can live in a body's
  shape or surface: leaves become a soft leaf-tip silhouette or a velvety moss texture, a pastry board becomes a
  flaky crust top. Motifs go into the prompt's "with ..." line (shape and surface only, never props or faces). If the board is other mascots, skip motifs and take their proportions instead.
- **Mood words:** two or three (calm, playful, premium, techy...). They steer shape softness and motion talk.

Keep it to a short paragraph plus the swatches.
No moodboard at all? Write the brief from the person's one-line idea. Ask "anything to change?" once, then go.

## 2. The cast

Ask how many agents and what each one does (or propose roles if the user only has a product idea). Give every
agent a clearly different silhouette so the set reads at 32px. Good, simple shapes:

| Shape | Reads as | Notes |
| --- | --- | --- |
| Sphere | calm, central, the main one | always works; good for a lead or orchestrator |
| Rounded triangle (point up) | direction, searching | good for scouts or finders |
| Soft flame (three plump tips) | energy, drive | tips must stay round; describe asymmetry |
| Rounded cube | solid, reliable, rules | front view only, so it reads as a rounded square |
| Three-bump cloud | gentle, caring, memory | don't say "cloud": describe the geometry |
| Pill or capsule (upright) | simple, friendly | close to the sphere at small sizes, so pair carefully |
| Teardrop (leaning) | eager, quick | close to the flame; don't use both |
| Rounded star (five soft points) | celebratory, special | keep points short and puffy |
| Bean or blob | playful, informal | easy to make look generic; give it a clear lean |

Rules: no two shapes that blur together at small sizes; one "hero" that is the simplest and most balanced (it gets
generated first and becomes the reference); no props, accessories or faces on any of them; eyes come from code.

Write the cast as a short list: name (becomes the file and agent name), role, shape, one line on personality.
Confirm it with the user.

## 3. Prompts

Build each prompt from the template in `prompts.md`: shape line + material + colour sentence + the fixed rules.
For every agent after the hero, add to the start of the prompt:
"Match the reference image exactly in material, surface finish, lighting, colours and rendering style; only the
shape is different:" and pass the hero's generation as the reference image (see `higgsfield.md`).
