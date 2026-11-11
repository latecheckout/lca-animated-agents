#!/usr/bin/env python3
"""Download generated images (for example Higgsfield results) into the kit, named by agent.

Usage:
  python fetch_images.py --out renders/ hero=https://.../a.png scout=https://.../b.png ...

Each argument is name=url; the file is saved as renders/<name>.png. If a download is blocked (the code sandbox
only reaches allowed domains), it says so and lists the links: ask the user to download those images and drop
them into the chat, named the same way, then carry on from the cutout step.
"""
import argparse, os, re, sys, urllib.request

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("items", nargs="+")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    failed = []
    for it in a.items:
        if "=" not in it:
            sys.exit(f"Expected name=url, got: {it}")
        name, url = it.split("=", 1)
        # names come from Claude, which may have read them off a web page: keep them to a plain file name
        name = re.sub(r"[^a-z0-9]+", "-", os.path.basename(name).lower()).strip("-")[:40] or "agent"
        if not url.startswith("https://"):
            failed.append((name, url, "only https:// links are allowed")); continue
        dst = os.path.join(a.out, name + ".png")
        try:
            with urllib.request.urlopen(url, timeout=20) as r, open(dst, "wb") as f:
                f.write(r.read())
            print(f"  saved {dst}")
        except Exception as e:
            failed.append((name, url, str(e)[:80]))
    if failed:
        print("\nBLOCKED: these could not be downloaded from here (network allowlist or expired link):")
        for name, url, err in failed:
            print(f"  {name}: {url}  ({err})")
        print("Ask the user to download them and upload them to the chat as <name>.png.")
        print("To make this automatic, an org admin can allow the image host's domain in Claude's code execution network settings.")
        sys.exit(2)

if __name__ == "__main__":
    main()
