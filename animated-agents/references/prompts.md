# Body image prompts

Rules that keep a set consistent:
- Body only: "completely blank with no eyes, no mouth, no face, no markings, no accessories". Eyes come from code.
- Same material, lighting, camera and background across the whole set. Generate one, then use it as the
  reference image for the rest.
- Strict front view, centred, whole body in frame with space around it.
- Background: pure black for glass, frosted, jelly or marble materials (the cutout reads glow against black);
  a transparent background for solid materials (with `gpt_image_2_5`, pass `background: "transparent"`), so a body
  that shares a colour with a plain backdrop never gets cut into.
- "No outer glow, no bloom, no shadow, no floor" so the cutout stays clean. Shadows and glow are added in code.
- Give each agent a clearly different silhouette (sphere, rounded triangle, flame, rounded cube, three-bump cloud,
  squat bean...) so they read at 32px.
- Keep bodies chunky: about as wide as tall, never more than 1.2x taller than wide. Tall pills, capsules and rods read
  as phallic, especially in glass with a vertical gradient.
- If a shape keeps coming out too detailed (clouds especially), don't name the object: describe the geometry
  ("one large round dome with two smaller round bumps on either side, flat bottom") and attach a simple black
  silhouette drawing as a shape reference.
- When revising a prompt for the user, always give the whole prompt, not just the changed part.

## Template

Replace the shape line and the colour sentence; keep the rest.

```
A minimalist mascot character body shaped like [SHAPE][, with THEME FEATURES], completely blank with no eyes, no mouth, no face, no arms, no legs, no feet, no limbs, no markings, no accessories. Strict front view, straight head-on, centered, symmetrical. [MATERIAL]. [COLOUR]. No outer glow, no bloom, no halo, no light spilling onto the background, crisp clean silhouette. No shadow, no floor, no reflection beneath. Flat pure black background. Premium designer toy aesthetic, calm and refined. Octane render quality, high resolution, noise-free.
```

`[, with THEME FEATURES]` is optional: body-only details from an idea or moodboard motif, e.g. "with gentle
vertical ribs like a pumpkin and a short curled stem on top".

## Materials (cutout mode in brackets)

- **Slightly frosted glass with shine** (glass): "Made of solid glass that is lightly frosted on the inside, mostly translucent with a soft milky haze within the glass, while the outer surface is perfectly smooth, polished and high-gloss like wet glass. Strong shine: crisp bright specular highlights on the upper left, a clean curved window reflection, sharp glints, and a bright thin rim of light along the edge."
- **Frosted glass** (glass): "Made entirely of solid frosted glass all the way through, like sandblasted or acid-etched glass, with a soft satin finish and very fine micro-grain texture. Light diffuses softly through it. Soft broad satin sheen and gentle highlights on the upper left, a faint soft rim along the edge."
- **Marble in glass** (marble): "Built in two layers like a marble inside glass: a thick outer shell of perfectly clear transparent glass, and inside it a soft frosted milky core that follows the same shape but sits inset from the edge, so a clear band of glass is visible all the way around."
- **Matte clay** (solid): "Made of smooth matte clay with a soft satin finish, gentle even studio lighting, subtle soft shading." Transparent background.
- **Jelly** (glass): "Made of soft wobbly translucent jelly, glossy and wet-looking, light glowing through it with a slightly denser colour toward the middle, crisp specular highlights on the upper left."
- **Plush** (solid): "Made of soft short-pile plush fabric like a premium designer toy, fine fuzzy texture catching the light, gentle soft studio lighting, subtle seams only where the shape needs them." Transparent background.
- **Glazed ceramic** (solid): "Made of glazed ceramic with a smooth glossy glaze, soft reflections and a clean bright highlight on the upper left, slightly pooled glaze toward the bottom." Transparent background.
- **Flat illustration** (solid): "A flat vector illustration with clean solid colour fills and one soft highlight, no gradients, no outlines." Transparent background.

## Colour sentence

Describe a soft vertical gradient inside the body, top to bottom, e.g. "The colour inside is a smooth seamless gradient, warm ivory cream near the top, melting into soft pale sky blue through the middle, with a muted sage green settling toward the bottom, all colours soft and muted, blending with very wide soft transitions, no patches, no spots, no splotches."
Match the product background: pull 3 or 4 colours from it.
By default the whole set shares one colour sentence. If the brief wants each agent in its own colour, write one
sentence per agent, and for agents 2+ swap the reference line for "Match the reference image exactly in material,
surface finish, lighting and rendering style, but NOT its colours" — otherwise the reference image pulls every agent
back to agent 1's palette. To change colours later without regenerating, use
`scripts/recolor.py`.
