#!/usr/bin/env python3
"""GTR70E WYVERN (fin control), headless dataset generator.

    python3 datagen.py outcomes --n 2000 --out datasets/outcomes.csv [--preset "Typical field"]
    python3 datagen.py traces   --n 50   --out datasets/traces.csv   --stride 4
    python3 datagen.py both     --n 500  --out datasets/run.csv       (writes run_outcomes / run_traces)
    options: --seed 0 --workers 7 --dt 0.001 --locked (fins locked: the passive baseline)
             --format csv|parquet (parquet needs pyarrow)

Each row of an outcomes file is one flight of wf_flightsim on a dispersed vehicle in a sampled
field condition (engine.py). Traces are the 200 Hz histories, decimated by --stride.
"""
from __future__ import annotations
import argparse, csv, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import engine as E

def _cell(v):
    if v is None: return "nan"
    if isinstance(v, (float, np.floating)): return "nan" if not math.isfinite(v) else f"{float(v):.6g}"
    return str(v)

class Writer:
    def __init__(self, path, cols, fmt="csv"):
        self.path, self.cols, self.fmt = path, cols, fmt
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        if fmt == "csv":
            self.f = open(path, "w", newline=""); self.w = csv.writer(self.f); self.w.writerow(cols)
        else:
            self.buf = {c: [] for c in cols}
    def rows(self, rs):
        for r in rs:
            if self.fmt == "csv": self.w.writerow([_cell(r.get(c)) for c in self.cols])
            else:
                for c in self.cols:
                    v = r.get(c); self.buf[c].append(float("nan") if v is None else float(v))
    def columns(self, d):
        n = len(next(iter(d.values())))
        if self.fmt == "csv":
            arr = np.column_stack([np.asarray(d[c], float) for c in self.cols])
            for i in range(n): self.w.writerow([_cell(x) for x in arr[i]])
        else:
            for c in self.cols: self.buf[c].extend(np.asarray(d[c], float).tolist())
    def close(self):
        if self.fmt == "csv": self.f.close()
        else:
            import pyarrow as pa, pyarrow.parquet as pq
            pq.write_table(pa.table({c: np.asarray(v) for c, v in self.buf.items()}), self.path)

def generate(kind, n, out, seed=0, envelope=None, workers=None, dt=0.001, stride=4, control=True,
             fmt="csv", progress=None, cancel=None, log=print):
    """kind: outcomes | traces | both. Returns the list of files written."""
    base, ext = os.path.splitext(out); ext = ".parquet" if fmt == "parquet" else ".csv"
    paths = {}
    if kind in ("outcomes", "both"): paths["o"] = (base + ("_outcomes" if kind == "both" else "") + ext)
    if kind in ("traces", "both"): paths["t"] = (base + ("_traces" if kind == "both" else "") + ext)
    wo = Writer(paths["o"], E.OUTCOME_COLS, fmt) if "o" in paths else None
    wt = Writer(paths["t"], E.TRACE_COLS, fmt) if "t" in paths else None
    conds = E.conditions(n, seed, envelope)
    t0 = time.time(); k = 0
    for row, tr in E.batch(conds, control=control, record=wt is not None, dt=dt, workers=workers,
                           progress=progress, cancel=cancel):
        if wo: wo.rows([row])
        if wt and tr is not None:
            wt.columns({c: v[::stride] for c, v in tr.items()})
        k += 1
    for w in (wo, wt):
        if w: w.close()
    log(f"{k} flights in {time.time() - t0:.1f} s -> " + ", ".join(paths.values()))
    return list(paths.values())

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["outcomes", "traces", "both"])
    ap.add_argument("--n", type=int, default=200); ap.add_argument("--out", default=os.path.join(HERE, "datasets", "run.csv"))
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--dt", type=float, default=0.001); ap.add_argument("--stride", type=int, default=4)
    ap.add_argument("--preset", default="Typical field", choices=list(E.PRESETS))
    ap.add_argument("--locked", action="store_true"); ap.add_argument("--format", default="csv", choices=["csv", "parquet"])
    a = ap.parse_args(argv)
    def prog(d, tot, rate):
        if d % max(1, tot // 20) == 0 or d == tot:
            print(f"  {d}/{tot}  {rate:.1f} flights/s  eta {(tot - d) / max(rate, 1e-6):.0f} s", flush=True)
    generate(a.kind, a.n, a.out, a.seed, E.PRESETS[a.preset], a.workers, a.dt, a.stride, not a.locked, a.format, prog)

if __name__ == "__main__":
    main()
