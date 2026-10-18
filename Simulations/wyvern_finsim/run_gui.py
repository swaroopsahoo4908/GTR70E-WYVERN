#!/usr/bin/env python3
"""Launch the GTR70E WYVERN fin-control Simulation & Dataset Suite.

macOS: use a Python with Tk 8.6 (Homebrew):
    /opt/homebrew/bin/python3 run_gui.py
One-time setup for that interpreter:
    /opt/homebrew/bin/python3 -m pip install numpy matplotlib pyarrow
Headless datasets without the GUI:  python3 datagen.py outcomes --n 2000 --out datasets/outcomes.csv
"""
import os, sys
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _preflight():
    missing = []
    for mod in ("numpy", "matplotlib"):
        try: __import__(mod)
        except ImportError: missing.append(mod)
    try: import tkinter  # noqa
    except Exception: missing.append("tkinter")
    if missing:
        exe = sys.executable
        print("\n[WYVERN finsim] this Python is missing:", ", ".join(missing), "\ninterpreter:", exe)
        if "tkinter" in missing: print("  brew install python-tk   # then use /opt/homebrew/bin/python3")
        pip = [m for m in missing if m != "tkinter"]
        if pip: print(f"  {exe} -m pip install {' '.join(pip)} pyarrow")
        sys.exit(1)

if __name__ == "__main__":
    _preflight()
    import gui
    gui.main()
