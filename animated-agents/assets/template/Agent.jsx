"use client";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { createAgent, defineAgents, setEffectColors } from "./agentRig.js";
import faces from "./agents.json";

// Register every agent's face settings and the effect colours once, from agents.json
defineAgents(faces.agents);
if (faces.effectColors) setEffectColors(faces.effectColors);

/**
 * <Agent name="scout" state="working" size={64} />
 * state: "idle" | "working" | "waiting" | "blocked" | "thinking" | "done" | "sleeping"
 * size:  pixels (bodies load the 512px file up to 128px, the 1024px file above)
 * glow:  0 (none, default) to about 2, a soft halo drawn in code
 * Call ref.current.bounce() for a one-off happy hop (nice when a task completes).
 */
export const Agent = forwardRef(function Agent(
  { name, state = "idle", size = 64, glow = 0, src, basePath = "/agents", interactive = true, className = "", style, ...rest },
  ref
) {
  const host = useRef(null);
  const inst = useRef(null);
  useEffect(() => {
    const a = createAgent(host.current, name, src || `${basePath}/${name}${size <= 128 ? "@512" : ""}.png`, { size, interactive, state, glow });
    inst.current = a;
    return () => { a.destroy(); inst.current = null; };
  }, [name, size, src, basePath, interactive]);
  useEffect(() => { inst.current?.setState(state); }, [state]);
  useEffect(() => { inst.current?.setGlow(glow); }, [glow]);
  useImperativeHandle(ref, () => ({ bounce: () => inst.current?.bounce() }), []);
  return <div ref={host} className={className} style={style} {...rest} />;
});

export default Agent;
