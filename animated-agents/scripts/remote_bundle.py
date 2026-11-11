#!/usr/bin/env python3
"""Print the one-line command that installs the kit builder in the person's Higgsfield sandbox.

Usage:
  python remote_bundle.py --zip agent-kit-bundle.zip   # the bundle as a zip, to host at a public URL (preferred)
  python remote_bundle.py            # fallback: prints a self-contained install command (about 23 KB)
  python remote_bundle.py --out f    # writes that command to a file instead

The command unpacks cutout.py, kit_remote.py and the animation engine (agentRig.js) into ~/agent-kit and prints
"installed". Run it once per sandbox; when a sandbox_exec result says sandbox_created: true, run it again.
"""
import argparse, base64, io, os, tarfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = {"cutout.py": os.path.join(HERE, "cutout.py"), "kit_remote.py": os.path.join(HERE, "kit_remote.py"),
         "agentRig.js": os.path.join(HERE, "..", "assets", "template", "agentRig.js")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--zip", help="write the bundle as a zip file instead (for hosting at a public URL)")
    a = ap.parse_args()
    if a.zip:
        with zipfile.ZipFile(a.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for name, path in FILES.items():
                z.write(path, name)
        print(f"Wrote {a.zip} ({os.path.getsize(a.zip) // 1024} KB)")
        return
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=9) as t:
        for name, path in FILES.items():
            t.add(path, arcname=name)
    b64 = base64.b64encode(buf.getvalue()).decode()
    cmd = f"mkdir -p ~/agent-kit && cd ~/agent-kit && echo '{b64}' | base64 -d | tar xz && echo installed"
    if a.out:
        open(a.out, "w").write(cmd)
        print(f"Wrote {a.out} ({len(cmd) // 1024} KB)")
    else:
        print(cmd)


if __name__ == "__main__":
    main()
