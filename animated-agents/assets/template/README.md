# __KIT__: animated agents

Live animated agents: each one is a PNG body with eyes and motion drawn in code. No video, no WebGL, and no
dependencies beyond React 18+ (the engine itself is plain JavaScript and works without React too).

Agents in this kit: __NAMES__

Open `preview.html` in any browser to see every agent in every state.

## Setup (React)

1. Copy this folder into the app, for example `src/components/__KIT__/`.
2. Copy `bodies/*.png` into the public folder at `/agents/` (or pass `basePath`).
3. Use it:

```jsx
import { Agent } from "./components/__KIT__/Agent.jsx";

<Agent name="__FIRST__" size={64} state={isBusy ? "working" : "idle"} />
```

Your bundler needs to import JSON (Vite, Next.js and Create React App all do by default).

## Props

| Prop | Values | Default |
| --- | --- | --- |
| `name` | an agent from `agents.json` | required |
| `state` | `idle` (looks around, blinks, small hops now and then), `thinking` (focused, tense, three-dot badge), `working` (soft, happy jumps one after another), `waiting` (drowsy, heavy eyes, sinking a little), `blocked` (startled, wide eyes, a "!" badge), `done` (one big celebratory jump, turning all the way around), `sleeping` | `idle` |
| `size` | pixels | `64` |
| `glow` | soft halo, `0` off to about `2` | `0` |
| `interactive` | eyes follow the pointer, click to hop | `true` |
| `basePath` | folder holding the body PNGs | `/agents` |
| `src` | override the body image URL | |

`ref.current.bounce()` gives a one-off hop, nice when a task completes.

## Without React

```js
import { createAgent, defineAgents } from "./agentRig.js";
import cfg from "./agents.json";
defineAgents(cfg.agents);
const a = createAgent(document.querySelector("#slot"), "__FIRST__", "/agents/__FIRST__@512.png", { size: 96 });
a.setState("working");
```

## Adjusting

- **Eye position and size** per agent: `agents.json`. `face` is the centre of the eyes as fractions of the body
  image (x, y), `dx` half the gap between them, `w` and `h` the eye size, `bottom` where the body meets the ground,
  `scale` a size nudge. Change, reload, check.
- Changing `state` and `glow` is instant; changing `name` or `size` remounts the agent.
- All agents share one animation loop, pause offscreen, and stay still for people with reduced motion turned on.
