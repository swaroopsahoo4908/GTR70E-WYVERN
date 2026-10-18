#!/usr/bin/env python3
"""Launch the GTR70E WYVERN Simulation & Dataset Suite GUI.

Recommended interpreter (macOS): Homebrew Python, which ships a modern Tk 8.6.
    /opt/homebrew/bin/python3 run_gui.py # Apple Silicon
    /usr/local/bin/python3 run_gui.py # Intel

One-time setup for that interpreter:
    /opt/homebrew/bin/python3 -m pip install numpy pyarrow
"""
import os, sys
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1") # hush macOS system-Tk deprecation notice
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _preflight():
    """Fail with a clear, copy-pasteable message instead of a raw ImportError traceback."""
    missing = []
    for mod in ("numpy", "matplotlib"):
        try: __import__(mod)
        except ImportError: missing.append(mod)
    try:
        import tkinter # noqa
    except Exception:
        missing.append("tkinter")
    if missing:
        exe = sys.executable
        print("\n[WYVERN datagen] This Python is missing:", ", ".join(missing))
        print("This interpreter:", exe)
        if "tkinter" in missing:
            print(" - tkinter is the GUI toolkit. Install a Tk-enabled Python:")
            print(" brew install python-tk # then use /opt/homebrew/bin/python3")
        pip = [m for m in missing if m != "tkinter"]
        if pip:
            print(f" - install packages into THIS interpreter:")
            print(f" {exe} -m pip install {' '.join(pip)} pyarrow")
        print(" Then re-run: {} run_gui.py".format(exe))
        print(" (Or skip the GUI and generate data headless: "
              "{} datagen.py outcomes --n 1000000 --out datasets/outcomes.parquet)\n".format(exe))
        sys.exit(1)


if __name__ == "__main__":
    _preflight()
    import gui
    gui.main()
