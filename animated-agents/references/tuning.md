# Tuning faces in agents.json

Every value is a fraction of the square body image (0 to 1), so it works at any size.

| Setting | What it does | Typical |
| --- | --- | --- |
| `face` | `[x, y]` centre point between the eyes | `[0.5, 0.55]` |
| `dx` | half the distance between the eyes | 0.12 to 0.16 |
| `w`, `h` | eye width and height | 0.07 to 0.09, 0.1 to 0.13 |
| `bottom` | where the body touches the ground (measured by the cutout) | 0.8 to 0.97 |
| `scale` | size nudge for this body | 1, wide shapes 1.1 to 1.2 |
| `mood` | resting eye shape, keep `neutral` | `neutral` |

Starting points by shape (then adjust from the close-ups):

| Shape | face | dx | w, h |
| --- | --- | --- | --- |
| Sphere | `[0.5, 0.55]` | 0.15 | 0.084, 0.125 |
| Rounded triangle | `[0.5, 0.665]` | 0.125 | 0.074, 0.108 |
| Flame | `[0.505, 0.665]` | 0.135 | 0.088, 0.104 |
| Rounded cube | `[0.5, 0.53]` | 0.16 | 0.088, 0.13 |
| Three-bump cloud | `[0.5, 0.6]` | 0.14 | 0.074, 0.1 (scale 1.14) |

How to judge a face: the eyes should sit slightly below the visual centre of the body's mass, not the centre of
the image; on clear glass, keep them over the coloured core, not the clear rim; at 32px the eyes must still read
as two dots. Small agents get a built-in 1.32x eye boost, so don't enlarge eyes just for small sizes.
