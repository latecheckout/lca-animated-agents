#!/usr/bin/env python3
"""Assemble the developer hand-off: a folder (and zip) with the React component, the engine, the bodies,
agents.json, an example, a README and the preview page.

Usage:
  python package_kit.py --kit agent-kit --out dist --name my-agents

Result: dist/my-agents/ and dist/my-agents.zip
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "assets", "template")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="agents")
    a = ap.parse_args()
    dst = os.path.join(a.out, a.name)
    kit, out = os.path.realpath(a.kit), os.path.realpath(dst)
    # Refuse anything that would overwrite the kit itself: the output is the kit, inside it, or contains it
    if out == kit or out.startswith(kit + os.sep) or kit.startswith(out + os.sep):
        sys.exit(f"Refusing to package into {dst}: it overlaps the kit at {a.kit}. Pick an --out outside the kit.")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.join(dst, "bodies"))
    for f in ("agentRig.js", "Agent.jsx"):
        shutil.copy(os.path.join(TPL, f), dst)
    shutil.copy(os.path.join(a.kit, "agents.json"), dst)
    for f in os.listdir(os.path.join(a.kit, "bodies")):
        shutil.copy(os.path.join(a.kit, "bodies", f), os.path.join(dst, "bodies"))
    if os.path.exists(os.path.join(a.kit, "preview.html")):
        shutil.copy(os.path.join(a.kit, "preview.html"), dst)
    names = list(json.load(open(os.path.join(a.kit, "agents.json")))["agents"])
    first = names[0] if names else "agent"
    ex = ["import { useRef, useState } from \"react\";", "import { Agent } from \"./Agent.jsx\";", "",
          "export default function Example() {", "  const [busy, setBusy] = useState(false);", "  const lead = useRef(null);", "  return (",
          "    <div style={{ display: \"flex\", gap: 24, alignItems: \"flex-end\", padding: 40 }}>",
          f"      <Agent ref={{lead}} name=\"{first}\" size={{120}} state={{busy ? \"working\" : \"idle\"}} />"]
    ex += [f"      <Agent name=\"{n}\" size={{48}} />" for n in names[1:]]
    ex += ["      <button onClick={() => setBusy((b) => !b)}>{busy ? \"Stop\" : \"Start working\"}</button>",
           "      <button onClick={() => lead.current.bounce()}>Hop</button>", "    </div>", "  );", "}", ""]
    open(os.path.join(dst, "Example.jsx"), "w").write("\n".join(ex))
    readme = open(os.path.join(TPL, "README.md")).read().replace("__NAMES__", ", ".join(f"`{n}`" for n in names)).replace("__FIRST__", first).replace("__KIT__", a.name)
    open(os.path.join(dst, "README.md"), "w").write(readme)
    shutil.make_archive(dst, "zip", a.out, a.name)
    print(f"Packaged {len(names)} agents into {dst}.zip")


if __name__ == "__main__":
    main()
