#!/bin/bash
# Double-click this file in Finder to open the GTR70E WYVERN Simulation & Dataset Suite.
# It picks the first Python that has a working GUI toolkit (Tk) + numpy.
cd "$(dirname "$0")" || exit 1
export TK_SILENCE_DEPRECATION=1

CANDIDATES=(/opt/homebrew/bin/python3 /usr/local/bin/python3 python3)
for PY in "${CANDIDATES[@]}"; do
  if command -v "$PY" >/dev/null 2>&1 && "$PY" -c "import tkinter, numpy, matplotlib" >/dev/null 2>&1; then
    echo "Launching with: $PY"
    exec "$PY" run_gui.py
  fi
done

echo "No Python found with both tkinter and numpy."
echo "Fix (Apple Silicon):"
echo "  brew install python-tk"
echo "  /opt/homebrew/bin/python3 -m pip install numpy pyarrow matplotlib"
echo "then double-click this file again."
read -r -p "Press Return to close…" _
