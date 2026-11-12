# Body image prompts

Rules that keep a set consistent but never samey:
- Write it as a toy, never as a body. Image safety filters read words literally, and "cute" next to "body",
  "bottom", "no clothing", "plump", "skin" or "wet" can get a harmless mascot blocked as NSFW. Say figure, base,
  middle, sides, surface, rounded and glossy instead, and never mention clothing. If Higgsfield still blocks one,
  retry once as a plain product shot: "Product photo of a small vinyl toy figurine shaped like [SHAPE], standing
  on its flat base…".
- Body only: "no eyes, no mouth and no face", with a smooth clear area on the front where the eyes go. Eyes (and,
  for the Kawaii and Smiley eye styles, the mouth) come from code. Top features such as leaves, ears, sprouts,
  horns or a tuft are part of the body and are welcome; arms, legs, props and clothing are not.
- Same material, lighting, camera and background across the whole set. Generate one, then use it as the
  reference image for the rest, but only for material and finish: the reference line must say not to copy its
  shape, proportions, top features or colours (see the template), or every agent comes back as agent 1 again.
- Strict front view, centred, whole body in frame with space around it.
- Background: pure black for glass, frosted, jelly or marble materials (the cutout reads glow against black);
  a transparent background for solid materials (with `gpt_image_2_5`, pass `background: "transparent"`), so a body
  that shares a colour with a plain backdrop never gets cut into.
- "No outer glow, no bloom, no shadow, no floor" so the cutout stays clean. Shadows and glow are added in code.
- Variety is the default; the user should never have to ask for it. Treat a cast like a designer's exploration
  sheet: every agent is a different character idea from the same theme. From "sprout", for example: a teardrop with
  two heart-shaped leaves, a tall drop with two long leaves, a mochi with a scalloped bottom and one sprout, a turnip
  with a pointed tip, a little ghost with a wavy hem and a leaf on top. Vary the body family, proportions, top
  features, bottom (flat, rounded, scalloped, pointed) and colours across the cast.
- Mix squat, round and taller bodies, but at most one tall agent, never more than 1.6x taller than wide, and tall
  bodies widen toward the bottom (a drop, a bell, a ghost). Never thin, straight-sided or rod-like: pills, capsules,
  rods and cylinders read as phallic, especially in glass with a vertical gradient.
- If a shape keeps coming out too detailed (clouds especially), don't name the object: describe the geometry
  ("one large round dome with two smaller round bumps on either side, flat bottom") and attach a simple black
  silhouette drawing as a shape reference.
- When revising a prompt for the user, always give the whole prompt, not just the changed part.

## Template

Replace the shape line and the colour sentence; keep the rest.

```
A designer-toy mascot figure shaped like [SHAPE][, with TOP FEATURES], standing on its flat base. It has no eyes, no mouth and no face (eyes are added later), with a smooth, clear area on the front where they will go. No arms, no legs, no feet, no props, no accessories, no text; its top features (leaves, ears, sprouts and the like) are part of the figure. Strict front view, straight head-on, centered. [MATERIAL]. [COLOUR]. No outer glow, no bloom, no halo, no light spilling onto the background, crisp clean silhouette. No shadow, no floor, no reflection beneath. Flat pure black background. Premium soft vinyl designer toy, playful and charming, with a distinctive silhouette. Octane render quality, high resolution, noise-free.
```

For agents 2 and up, put this in front of the prompt and attach agent 1 as the reference image:

```
Use the reference image only for the set's material, surface finish, lighting and rendering quality. Do NOT copy its shape, proportions, top features or colours: this character has its own shape and its own full, rich colours, described below.
```

`[, with TOP FEATURES]` carries the theme: details that are part of the body, from the idea or a moodboard motif,
e.g. "with two heart-shaped leaves on top" or "with gentle vertical ribs like a pumpkin and a short curled stem".

## Inspiration images

When the person gives inspiration images, send them to the image model with **every** agent as style references
(Higgsfield: `media_upload` the files, PUT the bytes, `media_confirm`, then pass each media id in `medias` with role
`image_references`; skip agent 1 as a reference in that case). Put this in front of each prompt so the cast takes
their look but stays a set of new characters:

```
The reference images are the user's style inspiration. Match their overall look closely: the material and surface finish, the colour palette, the lighting, the rendering style and the shape language. But make a new character, exactly as described below: do not copy their exact shape, and never copy a face, eyes, mouth, text or logos from them.
```

Plan with the images too: the material that fits them, each agent's colours from their palette, shapes in their shape
language, and still a different character idea per agent.

## Materials (cutout mode in brackets)

- **Slightly frosted glass with shine** (glass): "Made of solid glass that is lightly frosted on the inside, mostly translucent with a soft milky haze within the glass, while the outer surface is perfectly smooth, polished and high-gloss like polished glass. Strong shine: crisp bright specular highlights on the upper left, a clean curved window reflection, sharp glints, and a bright thin rim of light along the edge."
- **Frosted glass** (glass): "Made entirely of solid frosted glass all the way through, like sandblasted or acid-etched glass, with a soft satin finish and very fine micro-grain texture. Light diffuses softly through it. Soft broad satin sheen and gentle highlights on the upper left, a faint soft rim along the edge."
- **Marble in glass** (marble): "Built in two layers like a marble inside glass: a thick outer shell of perfectly clear transparent glass, and inside it a soft frosted milky core that follows the same shape but sits inset from the edge, so a clear band of glass is visible all the way around."
- **Matte clay** (solid): "Made of smooth matte clay with a soft satin finish, gentle even studio lighting, subtle soft shading." Transparent background.
- **Jelly** (glass): "Made of soft wobbly translucent jelly, glossy and dewy, light glowing through it with a slightly denser colour toward the middle, crisp specular highlights on the upper left."
- **Plush** (solid): "Made of soft short-pile plush fabric like a premium designer toy, fine fuzzy texture catching the light, gentle soft studio lighting, subtle seams only where the shape needs them." Transparent background.
- **Glazed ceramic** (solid): "Made of glazed ceramic with a smooth glossy glaze, soft reflections and a clean bright highlight on the upper left, slightly pooled glaze toward the bottom." Transparent background.
- **Flat illustration** (solid): "A flat vector illustration with clean solid colour fills and one soft highlight, no gradients, no outlines." Transparent background.

## Colour sentence

Describe a soft vertical gradient inside the body, top to bottom, e.g. "The colour inside is a smooth seamless gradient, warm ivory cream near the top, melting into soft pale sky blue through the middle, with a muted sage green settling toward the bottom, all colours soft and muted, blending with very wide soft transitions, no patches, no spots, no splotches."
Match the product background: pull 3 or 4 colours from it.
By default every agent gets its own colour sentence: stay in the theme's colour family so the set feels like one, but
give each agent a clearly different main hue or shade and its own accent (for sprouts: lime, mint, deep leaf green,
yellow-green with an orange tip). Only give every agent the same sentence when the brief explicitly asks for one
shared or matching colour. To change colours later without regenerating, use `scripts/recolor.py`.
