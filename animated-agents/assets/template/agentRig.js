// Animated agents engine: a PNG body per agent, eyes drawn in SVG, motion and effects in plain JS. No dependencies.
// States: idle, working, waiting, blocked, thinking, done (plus sleeping). One shared loop for every agent on the page.
// Each agent's face settings (fractions of its square body image): face = where the eyes centre, dx = half the gap
// between the eyes, w/h = eye size, bottom = where the body touches the ground, scale = body size tweak.
// eyeStyle: "classic" (tall pill eyes, the default), "kawaii" (big round eyes with a white rim, a shine and a tiny
// "w" mouth) or "smiley" (small dot eyes and a wide smile). It can change live: the next frame uses it.
// Register yours with defineAgents({ name: {...} }); anything missing falls back to DEFAULT_FACE.
const DEFAULT_FACE = { face: [0.5, 0.55], dx: 0.15, w: 0.084, h: 0.125, bottom: 0.97, mood: "neutral", scale: 1 };
const AGENTS = {};
export function defineAgents(table) { for (const k in table) AGENTS[k] = { ...DEFAULT_FACE, ...table[k] }; }
const INK = "#0A1834";
const NS = "http://www.w3.org/2000/svg";
const instances = [];
let uid = 0;
let reduce = { matches: false };
let started = false;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (c, t, k, dt) => c + (t - c) * (1 - Math.exp(-k * dt));

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

let cssDone = false;
function injectCss() { if (cssDone || typeof document === "undefined") return; cssDone = true; const st = document.createElement("style");
  st.textContent = `.agent{position:relative;display:inline-block;vertical-align:bottom;user-select:none;-webkit-user-select:none}
.agent .agent-body{position:absolute;will-change:transform}
.agent .agent-body img{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.agent .agent-glow{position:absolute;inset:0;overflow:hidden;-webkit-mask-size:100% 100%;mask-size:100% 100%;mix-blend-mode:screen;opacity:0;pointer-events:none}
.agent .agent-swirl{position:absolute;left:50%;top:58%;width:150%;height:150%;filter:blur(12px)}
.agent .agent-eyes{position:absolute;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}
.agent .agent-shadow{position:absolute;left:50%;bottom:-3%;width:62%;height:9%;border-radius:50%;background:radial-gradient(closest-side,var(--agent-shadow,#3A4A78),transparent);opacity:.3;pointer-events:none}
.agent-fx{position:absolute;pointer-events:none}
.agent-badge{position:absolute;pointer-events:none;opacity:0;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.82);box-shadow:0 4px 14px rgba(30,50,70,.18),inset 0 0 0 1px rgba(255,255,255,.9);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);transform-origin:20% 80%}
.agent-badge .bang{display:none;font-weight:800;color:#0A1834;line-height:1;font-family:system-ui,-apple-system,sans-serif}
.agent-badge .dots{display:none;gap:12%;width:70%;justify-content:center}
.agent-badge .dots i{display:block;width:22%;aspect-ratio:1;border-radius:50%;background:#0A1834;animation:agentDot 1s ease-in-out infinite}
.agent-badge .dots i:nth-child(2){animation-delay:.15s}.agent-badge .dots i:nth-child(3){animation-delay:.3s}
.agent-badge.alert .bang{display:block}.agent-badge.dots .dots{display:flex}
.agent-badge.dots{border-radius:999px;width:auto}
@keyframes agentDot{0%,60%,100%{transform:translateY(0);opacity:.45}30%{transform:translateY(-35%);opacity:1}}
@media (prefers-reduced-motion: reduce){.agent-badge .dots i{animation:none}}`;
  document.head.appendChild(st); }
export function createAgent(host, name, src, opts = {}) {
  start();
  const cfg = { ...DEFAULT_FACE, ...(AGENTS[name] || {}), ...(opts.face || {}) };
  const size = opts.size || 160;
  const id = "a" + uid++;
  host.classList.add("agent");
  host.style.width = host.style.height = size + "px";
  host.innerHTML = "";
  const shadow = document.createElement("div"); shadow.className = "agent-shadow"; host.appendChild(shadow);
  injectCss();
  const fxDpr = Math.min(typeof devicePixelRatio === "number" ? devicePixelRatio : 1, 2);
  // The colour-trail effects were retired, so no effect canvases are created (each one was 2.8x the agent's size).
  const fxB = null, fxF = null;
  const body = document.createElement("div"); body.className = "agent-body"; host.appendChild(body);
  const box = size * cfg.scale;
  Object.assign(body.style, { width: box + "px", height: box + "px", left: (size - box) / 2 + "px",
    bottom: -(1 - cfg.bottom) * box + "px", transformOrigin: `50% ${cfg.bottom * 100}%` });
  const img = document.createElement("img"); img.alt = ""; img.draggable = false; body.appendChild(img);
  img.addEventListener("load", () => measureBody(img, cfg)); img.src = src;
  const glow = document.createElement("div"); glow.className = "agent-glow";
  glow.style.webkitMaskImage = glow.style.maskImage = `url(${src})`;
  const swirl = document.createElement("div"); swirl.className = "agent-swirl"; glow.appendChild(swirl); body.appendChild(glow);
  const svg = el("svg", { viewBox: "0 0 100 100", class: "agent-eyes", "aria-hidden": "true" }, body);
  const eyes = [-1, 1].map((s) => {
    const cp = el("clipPath", { id: id + "c" + s }, svg); const poly = el("polygon", {}, cp);
    const g = el("g", {}, svg);
    const rim = el("ellipse", { fill: "#fff", "clip-path": `url(#${id}c${s})` }, g); // kawaii: white ring around the eye
    const ell = el("ellipse", { fill: INK, "clip-path": `url(#${id}c${s})` }, g);
    const arc = el("path", { fill: "none", stroke: INK, "stroke-linecap": "round" }, g);
    const glint = el("circle", { fill: "#fff", opacity: 0.85, "clip-path": `url(#${id}c${s})` }, g);
    const glint2 = el("circle", { fill: "#fff", opacity: 0.7, "clip-path": `url(#${id}c${s})` }, g);
    return { s, poly, rim, ell, arc, glint, glint2, cx: 0, cy: 0 };
  });
  const mouth = el("path", { fill: "none", stroke: INK, "stroke-linecap": "round", "stroke-linejoin": "round" }, svg);
  const mouthOpen = el("path", { fill: INK, stroke: INK, "stroke-linejoin": "round" }, svg); // open mouths: grin, "o"
  const badge = document.createElement("div"); badge.className = "agent-badge"; badge.setAttribute("aria-hidden", "true");
  badge.innerHTML = '<span class="bang">!</span><span class="dots"><i></i><i></i><i></i></span>';
  Object.assign(badge.style, { width: size * 0.3 + "px", height: size * 0.3 + "px", fontSize: size * 0.2 + "px", left: size * 0.74 + "px", top: size * 0.02 + "px" }); host.appendChild(badge);
  host.setAttribute("role", "img");
  const a = {
    host, name, cfg, size, body, shadow, glow, swirl, eyes, mouth, mouthOpen, mx: { w: 1, d: 1, o: 0, r: 0 }, img, spark: 0, pulse: 0, fxB, fxF, fxDpr, bx: null, fx: null, badge, jolt: -1, head: [0, 0], headV: [0, 0], wW: 0, wS: 0, hopT: 0, bp: Math.random(), visible: true, aura: opts.glow ?? 0, tA: (opts.tint && opts.tint.aura) || [170, 190, 210], tB: (opts.tint && opts.tint.aura2) || [235, 238, 242],
    state: opts.state || "idle", eyeK: size < 70 ? 1.32 : 1, mood: opts.mood || "default", interactive: opts.interactive !== false,
    t: Math.random() * 10, look: [0, 0], lookT: [0, 0], nextLook: 1 + Math.random() * 2,
    blinkAt: 1 + Math.random() * 3, blinkT: -1, idleHopAt: 3 + Math.random() * 5, idleHop: -1, glowV: 0, react: -1, hopN: 0, pointer: null,
    setState(s) { this.state = s; this.label(); },
    bounce() { this.react = 0; },
    destroy() { this.io && this.io.disconnect(); const i = instances.indexOf(this); if (i >= 0) instances.splice(i, 1); host.removeEventListener("click", onClick); host.innerHTML = ""; },
    setMood(m) { this.mood = m; },
    setGlow(v) { this.aura = v; },
    setTint(t) { if (t.aura) this.tA = t.aura; if (t.aura2) this.tB = t.aura2; if (t.swirl) swirl.style.background = t.swirl; },
    setSrc(u) { img.src = u; glow.style.webkitMaskImage = glow.style.maskImage = `url(${u})`; },
    label() { host.setAttribute("aria-label", `${name}, ${this.state || "idle"}`); },
  };
  a.label();
  if (opts.tint) a.setTint(opts.tint);
  if (typeof IntersectionObserver !== "undefined") { a.io = new IntersectionObserver(([en]) => { a.visible = en.isIntersecting; }); a.io.observe(host); }
  function onClick() { a.react = 0; }
  if (a.interactive) { host.style.cursor = "pointer"; host.addEventListener("click", onClick); }
  instances.push(a);
  return a;
}

// The turning hop sends the eyes around the body's real outline, so measure how wide the body is at eye height
// (and where its middle is) from the image itself. Runs once per image; explicit cfg.span/cfg.mid win if given.
function measureBody(img, cfg) {
  if (cfg.span != null && cfg.mid != null) return;
  try {
    const N = 160, c = document.createElement("canvas"); c.width = c.height = N;
    const x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(img, 0, 0, N, N);
    const y0 = Math.max(0, Math.round((cfg.face[1] - 0.03) * N)), y1 = Math.min(N - 1, Math.round((cfg.face[1] + 0.03) * N));
    const d = x.getImageData(0, y0, N, y1 - y0 + 1).data, rows = y1 - y0 + 1;
    let L = 0, R = 0, n = 0;
    for (let r = 0; r < rows; r++) { let l = -1, rr = -1;
      for (let i = 0; i < N; i++) if (d[(r * N + i) * 4 + 3] > 90) { if (l < 0) l = i; rr = i; }
      if (l >= 0) { L += l; R += rr + 1; n++; } }
    if (!n) return;
    L /= n * N; R /= n * N;
    cfg.mid = (L + R) / 2; cfg.span = (R - L) / 2;   // fractions of the image
  } catch (e) { /* cross-origin image without CORS: keep the default orbit */ }
}

function hop(u, H, k = 1) {
  // smooth hop: soft crouch, eased arc, gentle damped landing. k scales squash and stretch.
  const sm = (x) => x * x * (3 - 2 * x);
  if (u < 0.2) { const e = Math.sin(Math.PI * (u / 0.2)) * 0.5 + sm(u / 0.2) * 0.5;
    return { y: 0, sx: 1 + 0.07 * k * e, sy: 1 - 0.09 * k * e, a: 0 }; }
  if (u < 0.68) { const p = (u - 0.2) / 0.48, v = Math.cos(Math.PI * p);
    return { y: H * Math.sin(Math.PI * p), sx: 1 - 0.045 * k * v * Math.abs(v), sy: 1 + 0.075 * k * v * Math.abs(v), a: Math.sin(Math.PI * p) }; }
  // landing: a quick press that recovers without a wobble (critically damped, after bot-avatars' 'pulse')
  const q = (u - 0.68) / 0.32, kk = 7 * q, tail = q > 0.85 ? 1 - (q - 0.85) / 0.15 : 1;
  const e = (kk * kk * Math.exp(2 - kk)) / 4 * tail * tail * (3 - 2 * tail);
  return { y: 0, sx: 1 + 0.08 * k * e, sy: 1 - 0.1 * k * e, a: 0 };
}

function eyePath(e, cfg, mood, open, look, K = 1, spark = 0, turn = 0) {
  const s = e.s;
  // turning around (Grok-style spin): each eye rides around the body, squashing and hiding while it's on the back
  const mid = cfg.mid != null ? cfg.mid : cfg.face[0], span = Math.max(0.04, (cfg.span != null ? cfg.span : 0.38) - cfg.w * 0.55);
  const fa = Math.asin(Math.max(-1, Math.min(1, (cfg.face[0] + s * cfg.dx - mid) / span))) + turn, cosT = Math.cos(fa);
  const cx = 100 * ((turn ? mid + span * Math.sin(fa) : cfg.face[0] + s * cfg.dx) + look[0] * cfg.dx * 0.32 * cosT);
  const vis = turn ? Math.max(0, Math.min(1, cosT * 4)) : 1, squeeze = turn ? Math.max(0.2, Math.abs(cosT)) : 1;
  e.ell.style.opacity = e.arc.style.opacity = vis.toFixed(3);
  const cy = 100 * (cfg.face[1] + look[1] * cfg.h * 0.35);
  const rx = 50 * cfg.w * K * squeeze, ry0 = 50 * cfg.h * K, ry = ry0 * Math.max(open, 0.06);
  const showEll = mood !== "sleepy";
  const style = cfg.eyeStyle || "classic";
  e.ell.style.display = showEll ? "" : "none";
  e.arc.style.display = showEll ? "none" : "";
  e.glint.style.display = "none";
  let RX = rx, RY = ry;
  // kawaii: big, perfectly round eyes; smiley: small dots
  if (style === "kawaii") { const R = Math.max(rx, ry0) * 1.08; RX = R * squeeze; RY = R * Math.max(open, 0.06); }
  if (style === "smiley") { RX = rx * 0.78; RY = ry0 * 0.62 * Math.max(open, 0.06); }
  const custom = mood && typeof mood === "object" ? mood : null;
  if (mood === "wide") { RX = rx * 1.1; RY = ry0 * 1.14 * Math.max(open, 0.06); }
  if (mood === "excited") { RX = rx * 1.17; RY = ry0 * 1.24 * Math.max(open, 0.06); }
  if (custom) { RX = rx * custom.wide; RY = ry0 * custom.wide * 1.04 * Math.max(open, 0.06); }
  if (mood === "shock") { RX = rx * 1.24; RY = ry0 * 1.2 * Math.max(open, 0.06); }
  e.ell.setAttribute("cx", cx); e.ell.setAttribute("cy", cy); e.ell.setAttribute("rx", RX); e.ell.setAttribute("ry", RY);
  e.cx = cx; e.cy = cy; e.RX = RX; e.vis = vis; e.RYfull = RY / Math.max(open, 0.06);
  const rimOn = style === "kawaii" && showEll;
  e.rim.style.display = rimOn ? "" : "none";
  if (rimOn) { const w = RX * 0.2; e.rim.setAttribute("cx", cx); e.rim.setAttribute("cy", cy); e.rim.setAttribute("rx", RX + w); e.rim.setAttribute("ry", RY + w * Math.max(open, 0.06)); e.rim.style.opacity = vis.toFixed(3); }
  // lid clip: keep the area below a line; inner side = toward centre
  // lids are always level (never slanted, so nothing reads angry): a top lid keeps the part below a line,
  // a bottom lid (content) keeps the part above one
  const LID = { focus: [0.24, 0], down: [0.3, 0], up: [0.1, 0], heavy: [0.56, 0], narrow: [0.34, 0.2], content: [0, 0.32] }, x0 = cx - RX * 1.6, x1 = cx + RX * 1.6;
  const [lt, lb] = custom ? [custom.lid, 0] : LID[mood] || [0, 0], yl = lt ? cy - RY + 2 * RY * lt : cy - RY * 2, yb = lb ? cy + RY - 2 * RY * lb : cy + RY * 2;
  e.poly.setAttribute("points", `${x0},${yl} ${x1},${yl} ${x1},${yb} ${x0},${yb}`);
  const lidded = false;
  e.glint.setAttribute("cx", cx - s * RX * 0.05 - RX * 0.28 + look[0] * RX * 0.18); e.glint.setAttribute("cy", lidded ? cy + RY * 0.22 : cy - RY * 0.42); e.glint.setAttribute("r", RX * (lidded ? 0.22 : 0.27) * (1 + 0.35 * spark));
  e.glint2.style.display = "none";
  if (style === "kawaii" && showEll && open > 0.5) { e.glint.style.display = ""; e.glint.setAttribute("r", RX * 0.3 * (1 + 0.35 * spark)); e.glint.style.opacity = (0.9 * vis).toFixed(3); }
  e.glint2.setAttribute("cx", cx + RX * 0.3 + look[0] * RX * 0.15); e.glint2.setAttribute("cy", lidded ? cy + RY * 0.45 : cy + RY * 0.3); e.glint2.setAttribute("r", RX * 0.13 * spark);
  if (mood === "sleepy") {
    e.arc.setAttribute("fill", "none"); e.arc.setAttribute("stroke", INK);
    e.arc.setAttribute("d", `M${cx - rx * 1.05},${cy} Q${cx},${cy + ry0 * 0.45} ${cx + rx * 1.05},${cy}`);
    e.arc.setAttribute("stroke-width", rx * 0.5);
  }
}

// The mouth for the kawaii and smiley styles: centred under the eyes, it moves with them, hides on the turn and
// changes with the state. w = width, d = curve (1 smile, 0 flat), o = how open, r = how round (an "o").
function mouthTarget(a, perk, sigh, br) {
  if (a.react >= 0 && a.celebrate) return { w: 1.15, d: 1.2, o: 0.85, r: 0 };         // done: a big open grin
  if (a.react >= 0) return { w: 1.1, d: 1.2, o: 0.6, r: 0 };                            // a tap: a happy "ha"
  switch (a.state) {
    case "working": return { w: 1.04, d: 1.1, o: 0.12 + 0.4 * a.pulse, r: 0 };        // opens a little with every hop
    case "thinking": return { w: 0.45, d: 0, o: 0, r: 0 };                              // a small, flat, focused line
    case "waiting": return sigh > 0.3 ? { w: 0.32, d: 0, o: 0.8, r: 1 }                 // the sigh: a tiny "o"
      : { w: 0.55 + 0.45 * perk, d: 0.15 + 0.85 * perk, o: 0, r: 0 };                   // drowsy, then a smile on the perk
    case "blocked": return { w: 0.36, d: 0, o: 1, r: 1 };                               // startled "o"
    case "done": return { w: 1.15, d: 1.25, o: 0.2, r: 0 };
    case "sleeping": return { w: 0.24, d: 0, o: 0.55 + 0.2 * br, r: 1 };                // a small breathing "o"
    default: return { w: 1, d: 1, o: 0, r: 0 };
  }
}
function mouthPath(a, cfg, dt, perk, sigh, br) {
  const style = cfg.eyeStyle || "classic", m = a.mouth, mo = a.mouthOpen, [l, r] = a.eyes;
  if (style === "classic" || !l.vis) { m.style.display = mo.style.display = "none"; return; }
  const T = mouthTarget(a, perk, sigh, br), X = a.mx;
  for (const k of ["w", "d", "o", "r"]) X[k] = ease(X[k], T[k], 10, dt);
  const vis = Math.min(l.vis, r.vis).toFixed(3);
  const cx = (l.cx + r.cx) / 2, gap = Math.abs(r.cx - l.cx), eh = 50 * cfg.h;
  const kawaii = style === "kawaii";
  const base = kawaii ? gap * 0.32 : gap * 1.56;                                         // full mouth width at rest
  // Anchor under the lowest point of the eyes as they are right now (excited eyes grow, waiting eyes look down),
  // plus a fixed gap, so the mouth never touches them in any state
  const eyeBottom = Math.max(l.cy + (l.RYfull || 0), r.cy + (r.RYfull || 0));
  const y = Math.max(Math.max(l.cy, r.cy) + eh * (kawaii ? 0.55 : 1.05), eyeBottom + gap * (kawaii ? 0.1 : 0.2));
  const sw = Math.max(0.9, gap * (kawaii ? 0.045 : 0.06));
  const W = base * X.w / 2;
  m.setAttribute("stroke-width", sw); mo.setAttribute("stroke-width", sw * 0.6);
  if (X.r > 0.5) {
    // a round "o"
    const rx = Math.max(gap * 0.06, W * 0.5), ry = rx * (0.75 + 0.45 * X.o);
    mo.setAttribute("d", `M${cx - rx},${y} a${rx},${ry} 0 1,0 ${2 * rx},0 a${rx},${ry} 0 1,0 ${-2 * rx},0`);
    mo.style.display = ""; m.style.display = "none"; mo.style.opacity = vis; return;
  }
  if (X.o > 0.06) {
    // open: a flat-ish top edge and a deeper bottom edge, like a grin
    // the open shape is narrower than the line smile and its depth follows the eye gap, so it never swallows the face
    const Wo = kawaii ? W : W * 0.62, top = Wo * 0.14 * X.d;
    const bot = (kawaii ? Wo * 0.8 : gap * 0.3) * (0.35 + 0.65 * X.o) * Math.max(0.3, X.d);
    mo.setAttribute("d", `M${cx - Wo},${y} Q${cx},${y + top} ${cx + Wo},${y} Q${cx},${y + bot * 2} ${cx - Wo},${y} Z`);
    mo.style.display = ""; m.style.display = "none"; mo.style.opacity = vis; return;
  }
  mo.style.display = "none"; m.style.display = ""; m.style.opacity = vis;
  if (kawaii) {
    // a tiny "w": two small bumps, flattening out as d goes to 0
    const w = W, h = w * 0.9 * X.d;
    m.setAttribute("d", `M${cx - w},${y} q${w / 2},${h} ${w},0 q${w / 2},${h} ${w},0`);
  } else {
    // smiley: a wide, soft U that flattens and narrows with the state
    m.setAttribute("d", `M${cx - W},${y} Q${cx},${y + W * 0.7 * X.d} ${cx + W},${y}`);
  }
}

function step(a, dt) {
  a.t += dt; const t = a.t, cfg = a.cfg, still = reduce.matches;
  const sleeping = a.state === "sleeping", working = a.state === "working";
  const thinking = a.state === "thinking", waiting = a.state === "waiting", blocked = a.state === "blocked", done = a.state === "done";
  if (a.prevState !== a.state) { if (done) { a.react = 0; a.celebrate = true; a.burstDone = false; } if (blocked) a.jolt = 0; a.prevState = a.state; }
  let mood = a.mood === "default" ? cfg.mood : a.mood;
  if (a.seed == null) a.seed = Math.random();
  let perk = 0, sigh = 0;
  if (waiting) { const c = (t + a.seed * 4) % 5.4; // drowsy, then a sudden perk up (latching on), then let down
    if (c > 1.5 && c < 1.68) perk = (c - 1.5) / 0.18; else if (c >= 1.68 && c < 2.75) perk = 1; else if (c >= 2.75 && c < 4.0) { const v = (c - 2.75) / 1.25; perk = 1 - v * v * (3 - 2 * v); sigh = Math.sin(Math.PI * v); } }
  if (a.mood === "default") { if (working) mood = "excited"; else if (thinking) mood = "narrow"; else if (waiting) mood = { lid: 0.56 * (1 - perk), wide: 1 + 0.17 * perk }; else if (blocked) mood = "shock"; else if (done) mood = "content"; }
  if (a.wS > 0.5) mood = "sleepy";
  // look target
  if (a.pointer && a.interactive && !sleeping && !blocked && !thinking) { a.lookT = a.pointer; }
  else if (working) { a.lookT = [0, -0.2]; }
  else if (thinking) { a.lookT = [0, -0.05]; }
  else if (waiting) { a.lookT = perk > 0.05 ? [0.32 * Math.sin(t * 5.3 + a.seed * 9) * perk, -0.08 * perk] : [Math.sin(t * 0.5) * 0.15, 0.3]; }
  else if (blocked) { a.lookT = [0.85, -0.9]; }
  else if (done) { a.lookT = [0, -0.1]; }
  else if (!sleeping) {
    a.nextLook -= dt;
    if (a.nextLook <= 0) { a.nextLook = 1.6 + Math.random() * 2.2;
      a.lookT = Math.random() < 0.35 ? [0, 0] : [(Math.random() * 2 - 1), (Math.random() * 0.8 - 0.4)]; }
  } else a.lookT = [0, 0.2];
  // eyes dart quickly; the head follows on a lightly damped spring (eyes lead, head after)
  a.look = [ease(a.look[0], a.lookT[0], 14, dt), ease(a.look[1], a.lookT[1], 14, dt)];
  { const w = 6.4, z = 0.9; for (let i = 0; i < 2; i++) { a.headV[i] += (w * w * (a.look[i] - a.head[i]) - 2 * z * w * a.headV[i]) * dt; a.head[i] += a.headV[i] * dt; } }
  // state weights blend in and out instead of snapping
  a.wW = ease(a.wW, working ? 1 : 0, 2.6, dt); a.wS = ease(a.wS, sleeping ? 1 : 0, 1.6, dt);
  a.wT = ease(a.wT || 0, thinking ? 1 : 0, 2.6, dt); a.wA = ease(a.wA || 0, waiting ? 1 : 0, 2.6, dt); a.wB = ease(a.wB || 0, blocked ? 1 : 0, 2.2, dt);
  // blink
  let open = 1;
  if (a.wS < 0.5) {
    a.blinkAt -= dt;
    if (a.blinkAt <= 0 && a.blinkT < 0) { a.blinkT = 0; a.doubleBlink = Math.random() < 0.25; }
    if (a.blinkT >= 0) { a.blinkT += dt; const d = waiting ? 0.42 : 0.16, n = a.doubleBlink ? 2 : 1, p = a.blinkT / d;
      if (p < n) open = 1 - Math.sin(Math.PI * (p % 1));
      else { a.blinkT = -1; a.blinkAt = waiting ? 3.5 + Math.random() * 2 : 2.2 + Math.random() * 3.2; } }
  }
  // body motion
  if (!working) a.pulse = ease(a.pulse, 0, 6, dt);
  const awake = 1 - a.wS, idleW = Math.max(0, 1 - a.wW - a.wS);
  let spin = 0, turn = 0, y = -0.008 * a.wS;
  if (!working) a.whoosh = null;
  let sx = 1, sy = 1, rot = a.head[0] * 2.4 * awake * (1 - a.wW), xs = a.head[0] * 0.012 * awake * (1 - a.wW);
  // breathing always, slower and deeper asleep (phase integrated so speed changes never jump)
  a.bp += dt / (3.0 + 1.4 * a.wS); const br = Math.sin(a.bp * 2 * Math.PI);
  sy += br * (0.016 + 0.01 * a.wS); sx -= br * (0.011 + 0.006 * a.wS);
  if (open < 1 || a.wS > 0) open *= Math.max(0.06, 1 - 1.6 * a.wS);
  if (a.wW > 0.02 && !still) { a.hopT += dt;
    // working: happy, soft jumps, one after another
    const T = 0.8, p = (a.hopT % T) / T, n = Math.floor(a.hopT / T), h = hop(p, 0.13 * a.wW, 0.9 * a.wW);
    y += h.y; sx *= h.sx; sy *= h.sy; rot += (n % 2 ? 1 : -1) * 2 * h.a * a.wW; a.pulse = h.a;
    open *= (1 + 0.1 * h.a) * (1 - 2.2 * Math.max(0, 1 - h.sy));
    if (mood !== "sleepy") mood = "excited"; }
  else if (a.wW <= 0.02) a.hopT = Math.random() * 0.6; // a random start so a row of agents doesn't whoosh in unison
  if (idleW > 0.5 && a.state === "idle") {
    a.idleHopAt -= dt;
    if (a.idleHopAt <= 0 && a.idleHop < 0) { a.idleHop = 0; a.idleHops = Math.random() < 0.4 ? 2 : 1; }
    if (a.idleHop >= 0) { a.idleHop += dt; const D = 0.85, p = a.idleHop / D;
      if (p >= a.idleHops) { a.idleHop = -1; a.idleHopAt = 4 + Math.random() * 5; }
      else { const h = hop(p % 1, 0.08, 0.7); y = h.y; sx = h.sx; sy = h.sy; rot += 2 * h.a * (Math.floor(p) % 2 ? -1 : 1); } } }
  if (!still) {
    // thinking: scrunches down and tenses, with a faint tremble
    if (a.wT > 0.01) { sy -= 0.075 * a.wT; sx += 0.05 * a.wT; y -= 0.004 * a.wT; rot += Math.sin(t * 38) * 0.6 * a.wT; }
    // waiting: drowsy, a slow deep breath and a gentle sway, sinking a little
    if (a.wA > 0.01) { const b = Math.sin(t * 1.1); sy += (0.02 * b * (1 - perk) - 0.025 + 0.06 * perk - 0.05 * sigh) * a.wA; sx -= (0.012 * b * (1 - perk) + 0.03 * perk - 0.03 * sigh) * a.wA;
      y += 0.01 * perk * a.wA; rot += (1.6 * Math.sin(t * 0.6) * (1 - perk) - 2 * sigh) * a.wA; }
    // blocked: a startled jolt on arrival, then rigid with a slight lean back
    if (a.wB > 0.01) { if (a.jolt >= 0) { a.jolt += dt; const p = a.jolt / 0.5; if (p >= 1) a.jolt = -1; else { const h = hop(p, 0.06, 1.3); y += h.y; sx *= h.sx; sy *= h.sy; } }
      sy += 0.03 * a.wB; sx -= 0.02 * a.wB; rot -= 2.5 * a.wB; }
  }
  if (a.react >= 0) { a.react += dt; const big = !!a.celebrate, p = a.react / (big ? 1.5 : 1.25);
    if (p >= 1) { a.react = -1; a.celebrate = false; a.whoosh = null; }
    else { const h = hop(p, big ? 0.42 : 0.24, big ? 1.25 : 1.0); y = h.y; sx = h.sx; sy = h.sy; rot = 5 * h.a;
      if (big) { const q = clamp((p - 0.18) / 0.5, 0, 1); turn = Math.PI * 2 * q * q * (3 - 2 * q); a.whoosh = { p: clamp((p - 0.06) / 0.86, 0, 1), w: 1, all: true }; }
      if (!sleeping) mood = "content"; } }
  if (still) { y = 0; sx = sy = 1; rot = 0; spin = 0; turn = 0; a.whoosh = null; }
  const S = a.size;
  const hc = (cfg.bottom - 0.5) * S * cfg.scale; // spin around the middle of the body, not its feet
  a.body.style.transform = `translate(${xs * S}px, ${-y * S}px)` + (spin ? ` translate(0, ${-hc}px) rotate(${spin}deg) translate(0, ${hc}px)` : "") + ` rotate(${rot}deg) scale(${sx}, ${sy})`;
  const hy = clamp(y / 0.24, 0, 1);
  a.shadow.style.transform = `translateX(-50%) scale(${(1 - 0.4 * hy) * sx}, ${1 - 0.3 * hy})`;
  a.shadow.style.opacity = (0.32 * (1 - 0.6 * hy)).toFixed(3);
  // glow
  a.glowV = ease(a.glowV, working ? 1 : 0, 3, dt);
  const g = a.glowV, pz = a.pulse * g;
  a.glow.style.opacity = "0"; // no inner glow while working, per client
  const au = a.aura * (0.3 + 0.7 * g + 0.35 * pz), gr = (a.size * (0.05 + 0.07 * g + 0.04 * pz)).toFixed(1);
  const auraF = au > 0.01 ? ` drop-shadow(0 0 ${gr}px rgba(${a.tA},${Math.min(0.9, 0.55 * au).toFixed(3)})) drop-shadow(0 0 ${(gr * 0.35).toFixed(1)}px rgba(${a.tB},${Math.min(0.8, 0.45 * au).toFixed(3)}))` : "";
  a.img.style.filter = auraF;
  a.spark = ease(a.spark, working ? 0.6 + 0.4 * a.pulse : 0, 8, dt);
  a.swirl.style.transform = `translate(-50%,-50%) rotate(${(t * 70) % 360}deg)`;
  a.eyes.forEach((e) => eyePath(e, cfg, mood, Math.max(open, 0.08), a.look, a.eyeK * (1 + 0.06 * a.glowV), a.spark, turn));
  mouthPath(a, cfg, dt, perk, sigh, br);
  drawFx(a, dt, t, y, still);
  const bk = blocked ? "alert" : thinking ? "dots" : null;
  if (bk && a.badgeKind !== bk) { a.badgeKind = bk; a.badge.className = "agent-badge " + bk; a.badgeS = 0; a.badgeT = 0;
    Object.assign(a.badge.style, bk === "dots" ? { width: S * 0.44 + "px", height: S * 0.24 + "px", left: S * 0.7 + "px" } : { width: S * 0.3 + "px", height: S * 0.3 + "px", left: S * 0.74 + "px" }); }
  a.badgeS = ease(a.badgeS || 0, bk ? 1 : 0, bk ? 9 : 14, dt); a.badgeV = (a.badgeV || 0);
  const bs = bk ? 1 - Math.exp(-6 * (a.badgeT = (a.badgeT || 0) + dt)) * Math.cos(14 * a.badgeT) : a.badgeS; if (!bk) a.badgeT = 0;
  a.badge.style.opacity = a.badgeS.toFixed(3); a.badge.style.transform = `translate(0, ${-y * S}px) scale(${Math.max(0, bk ? bs : a.badgeS).toFixed(3)})`;
}

// ---- effects: an energy spiral while working, a burst when done
const GLOW = (() => { if (typeof document === "undefined") return null; const c = document.createElement("canvas"); c.width = c.height = 64; const x = c.getContext("2d"), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.25, "rgba(225,240,255,.9)"); g.addColorStop(0.6, "rgba(150,200,240,.35)"); g.addColorStop(1, "rgba(150,200,240,0)"); x.fillStyle = g; x.fillRect(0, 0, 64, 64); return c; })();
const ORBITS_DONE = []; let STRIPES = ["#3F6E96", "#5B8DB8", "#86B6D3", "#5E9C8C", "#7DB38A", "#A4C79A", "#4E8277"];
const ORBITS = [{ tilt: 1.32, roll: -0.1, dir: 1 }];
// done: four orbits at different angles, alternating direction, each a few strands, so colour wraps the agent from all sides
ORBITS_DONE.push({ tilt: 1.32, roll: -0.1, dir: 1, start: -1.6 }, { tilt: 0.5, roll: 0.95, dir: -1, start: 0.4 }, { tilt: 0.5, roll: -0.95, dir: 1, start: 2.2 }, { tilt: 0.25, roll: 1.62, dir: -1, start: -0.6 });
function splitDone() { ORBITS_DONE.forEach((o, i) => (o.cols = STRIPES.filter((_, j) => (j + i) % 2 === 0))); }
splitDone();
/** Kept for compatibility: the colour-trail effects these coloured were retired, so this has no visible effect. */
export function setEffectColors(cols) { if (Array.isArray(cols) && cols.length) { STRIPES = cols.slice(); splitDone(); } }
// a bundle of rainbow strands sweeping around the body on a tilted orbit, a rounded tip leading and the tail trailing;
// the half of the orbit behind the body is drawn under it. p runs 0..1 over one sweep
const rnd = (a, b) => { const v = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return v - Math.floor(v); };
function whoosh(a, p, w, cx, cy, k, orb = ORBITS[0]) {
  const cols = orb.cols || STRIPES, M = 28, oi = orb.start ?? 0, base = k * 0.56;
  for (let st = 0; st < cols.length; st++) {
    // each strand: its own delay, speed, length, thickness, slightly different orbit, and a gentle wave
    const r1 = rnd(st, 1 + oi), r2 = rnd(st, 2 + oi), r3 = rnd(st, 3 + oi), r4 = rnd(st, 4 + oi), r5 = rnd(st, 5 + oi), r6 = rnd(st, 6 + oi);
    const delay = r1 * 0.2, pi = clamp((p - delay) / 0.8, 0, 1);
    if (pi <= 0 || pi >= 1) continue;
    const speed = 0.82 + r2 * 0.4, head = (orb.start ?? -Math.PI * 0.5) + orb.dir * pi * Math.PI * 2.3 * speed;
    const tail = Math.min(2.4, 0.4 + pi * 5) * (1 - Math.max(0, pi - 0.72) / 0.28 * 0.85) * (0.7 + r3 * 0.6);
    const tilt = orb.tilt + (r4 - 0.5) * 0.4, roll = orb.roll + (r5 - 0.5) * 0.34, cr = Math.cos(roll), sr = Math.sin(roll);
    const R = base * (0.9 + r6 * 0.24) + (st - (cols.length - 1) / 2) * k * 0.018, waveA = k * 0.04 * (r2 - 0.5), waveP = r3 * 6.28;
    const fade = w * (pi < 0.1 ? pi / 0.1 : pi > 0.82 ? (1 - pi) / 0.18 : 1), thick = k * 0.078 * (0.75 + r4 * 0.5);
    let prev = null;
    for (let m = 0; m <= M; m++) { const u = m / M, th = head - orb.dir * u * tail;
      const x = Math.cos(th) * R, yy = Math.sin(th) * Math.cos(tilt) * R, z = Math.sin(th) * Math.sin(tilt);
      const X = cx + x * cr - yy * sr, Y = cy - k * 0.02 + x * sr + yy * cr + waveA * Math.sin(th * 2 + waveP);
      if (prev) { const ctx = (z + prev.z) / 2 < 0 ? a.bx : a.fx;
        ctx.globalAlpha = fade * (z < 0 ? 0.8 : 1); ctx.strokeStyle = cols[st]; ctx.lineCap = "round"; ctx.lineWidth = thick * (1 - u * 0.65);
        ctx.beginPath(); ctx.moveTo(prev.X, prev.Y); ctx.lineTo(X, Y); ctx.stroke(); }
      prev = { X, Y, z }; }
  }
  a.bx.globalAlpha = a.fx.globalAlpha = 1;
}
function burst(a) { const N = 16; a.parts = a.parts || [];
  for (let i = 0; i < N; i++) a.parts.push({ ang: (i / N) * Math.PI * 2 + 0.1, col: STRIPES[i % 4], life: 0, max: 0.7 }); }
function drawFx(a, dt, t, y, still) {
  if (!a.fxB) return;   // effects retired: nothing to draw
  const S = a.size, d = a.fxDpr, W = a.fxB.width, cx = W / 2, cy = W / 2 + (0.5 - 0.5) * S * d - y * S * d;
  const busy = (a.parts && a.parts.length) || (a.rings && a.rings.length);   // colour-strand whoosh retired: working/done move without trails
  if (!busy) { if (a.fxDirty) { a.bx.clearRect(0, 0, W, W); a.fx.clearRect(0, 0, W, W); a.fxDirty = false; } return; }
  a.fxDirty = true; a.bx.clearRect(0, 0, W, W); a.fx.clearRect(0, 0, W, W);
  if (still) return;
  const k = S * d;
  if (a.parts && a.parts.length) { a.parts = a.parts.filter((p) => (p.life += dt) < p.max);
    for (const p of a.parts) { const q = p.life / p.max, e = 1 - Math.pow(1 - q, 3), r0 = k * (0.42 + 0.55 * e), r1 = r0 + k * 0.26 * (1 - q);
      a.fx.globalAlpha = 1 - q * q; a.fx.strokeStyle = p.col; a.fx.lineCap = "round"; a.fx.lineWidth = k * 0.05 * (1 - 0.6 * q);
      a.fx.beginPath(); a.fx.moveTo(cx + Math.cos(p.ang) * r0, cy - k * 0.1 + Math.sin(p.ang) * r0 * 0.9); a.fx.lineTo(cx + Math.cos(p.ang) * r1, cy - k * 0.1 + Math.sin(p.ang) * r1 * 0.9); a.fx.stroke(); }
    a.fx.globalAlpha = 1; }
  if (a.rings && a.rings.length) { a.rings = a.rings.filter((r) => (r.life += dt) < 0.6);
    for (const r of a.rings) { const p = r.life / 0.6; a.fx.globalAlpha = (1 - p) * 0.7; a.fx.strokeStyle = "rgba(235,245,255,1)"; a.fx.lineWidth = k * 0.025 * (1 - p);
      a.fx.beginPath(); a.fx.ellipse(cx, cy - k * 0.1, k * (0.35 + 0.45 * p), k * (0.3 + 0.38 * p), 0, 0, Math.PI * 2); a.fx.stroke(); } a.fx.globalAlpha = 1; }
}


let last = 0;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 1 / 20); last = now;
  for (const a of instances) if (a.host.isConnected && a.visible) step(a, dt);
  requestAnimationFrame(loop);
}
function onMove(ev) {
  for (const a of instances) {
    if (!a.interactive) continue;
    const r = a.host.getBoundingClientRect(); const cx = r.left + r.width / 2, cy = r.top + r.height * a.cfg.face[1];
    const dx = ev.clientX - cx, dy = ev.clientY - cy, d = Math.hypot(dx, dy);
    a.pointer = d < r.width * 1.6 ? [clamp(dx / (r.width * 0.9), -1, 1), clamp(dy / (r.width * 0.9), -1, 1)] : null;
  }
}
function start() {
  if (started || typeof window === "undefined") return; started = true;
  reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  window.addEventListener("pointermove", onMove, { passive: true });
  document.documentElement.addEventListener("pointerleave", () => instances.forEach((a) => (a.pointer = null)));
  last = performance.now(); requestAnimationFrame(loop);
}

export const agentNames = () => Object.keys(AGENTS);
