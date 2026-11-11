#!/usr/bin/env python3
"""Check that this machine has what the skill needs, and say exactly how to install anything missing.

Usage:
  python check_setup.py

Required: Python 3.9+, Pillow, NumPy, SciPy (cutouts, colours, previews) and Node (bundles the preview).
Optional: Playwright + Chromium (automatic visual checks). The Higgsfield connector is checked by Claude, not here.
"""
import importlib.util, shutil, sys

ok = True
def line(good, what, fix=""):
    global ok
    print(("  ok    " if good else "  MISSING ") + what + ("" if good else f"\n          fix: {fix}"))

print("Animated agents: setup check")
line(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]} (3.9+)", "install Python 3.9 or newer from python.org")
missing = [m for m in ("PIL", "numpy", "scipy") if importlib.util.find_spec(m) is None]
line(not missing, "Pillow, NumPy, SciPy", f"{sys.executable} -m pip install pillow numpy scipy")
ok = ok and not missing and sys.version_info >= (3, 9)
node = shutil.which("node")
line(bool(node), "Node (for the preview build)", "install Node 18+ from nodejs.org")
ok = ok and bool(node)
pw = importlib.util.find_spec("playwright") is not None
line(pw, "Playwright (optional: automatic screenshots of the preview)", f"{sys.executable} -m pip install playwright && {sys.executable} -m playwright install chromium")
print("\nReady." if ok else "\nInstall the missing pieces above, then run this again.")
sys.exit(0 if ok else 1)
