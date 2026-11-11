# States and how they move

All motion lives in `agentRig.js`, in `step()` (body and eyes). There are no particle or colour-trail effects. Motion is
springy and eased: states blend in and out over about a second instead of snapping.

| State | Eyes | Body | Extras |
| --- | --- | --- | --- |
| `idle` | open, blink every few seconds (sometimes twice), glance around, follow the pointer | slow breathing, small lean toward where it looks, an occasional small hop | none |
| `thinking` | narrowed, level lids top and bottom, looking ahead | scrunched down and tense, faint tremble | three-dot badge, top right |
| `working` | big and wide, excited | soft, happy jumps one after another (0.8s each), a slight sway; no spin | none |
| `waiting` | heavy and drowsy, then suddenly wide and darting, then sinking back | drowsy sway; perks up and rises; a disappointed sigh and slump | none |
| `blocked` | wide, shocked, looking up at the badge | startled jolt on arrival, then stiff, leaning back | "!" badge, top right |
| `done` | soft and content | one big celebratory jump, turning all the way around; the eyes ride the body's measured outline | none |
| `sleeping` | closed | slow, deep breathing | none |

Design rules the client feedback taught (keep them):
- Lids are always level. Slanted lids read as angry or evil.
- No white glints in the eyes; they read too cute.
- No colour trails or particles around the body (removed after feedback); motion carries the state.
- Keep motion smooth and soft rather than bouncy; it should never feel volatile.

Common changes:
- Working rhythm: in `step()`, `T` (seconds per jump, 0.8) and the hop height (0.13).
- Turn width: `measureBody()` reads each body's width at eye height from its image (`cfg.mid`, `cfg.span`); set them in
  `agents.json` to override.
- Waiting loop: in `step()`, the `perk` timings (drowsy, perk up, hold, sigh) over a 5.4s cycle.
- Badge look: the injected CSS in `injectCss()` (`.agent-badge`).
After any change, rebuild the preview and re-run the check.
