#!/usr/bin/env python3
"""
GTR70E WYVERN, dataset loading + plot building (backend-agnostic, no Tk).

These are pure functions so they can be unit-tested headless; the GUI embeds the returned
matplotlib Figure with FigureCanvasTkAgg. Reads Parquet (pyarrow) or (gzip-)CSV, samples large
sets to keep plotting responsive, and builds five plot kinds used across the three dataset types.
"""
import os, gzip
import numpy as np
from matplotlib.figure import Figure

PLOT_KINDS = ["Histogram", "Scatter", "Density (hexbin)", "Trajectories", "Correlation heatmap"]


# ------------------------------------------------------------------ loading
def load_dataset(path, max_load_rows=2_000_000, seed=0):
    """Load a dataset into {col: np.ndarray}. Evenly subsamples if it exceeds max_load_rows.
    Returns (data, cols, n_total, n_loaded)."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if path.endswith(".parquet"):
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        n_total = pf.metadata.num_rows
        t = pq.read_table(path)
        cols = t.column_names
        if n_total > max_load_rows:
            idx = np.linspace(0, n_total - 1, max_load_rows).astype(np.int64)
            t = t.take(idx)
        data = {c: np.asarray(t.column(c).to_numpy(zero_copy_only=False), dtype=float) for c in cols}
    else: # csv / csv.gz
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt") as fh:
            cols = fh.readline().strip().split(",")
        raw = np.loadtxt(path, delimiter=",", skiprows=1) # numpy auto-handles .gz
        if raw.ndim == 1:
            raw = raw.reshape(1, -1)
        n_total = raw.shape[0]
        if n_total > max_load_rows:
            idx = np.linspace(0, n_total - 1, max_load_rows).astype(np.int64)
            raw = raw[idx]
        data = {c: raw[:, i] for i, c in enumerate(cols)}
    n_loaded = len(next(iter(data.values()))) if data else 0
    return data, cols, n_total, n_loaded


def numeric_cols(data):
    return [c for c, v in data.items() if np.issubdtype(np.asarray(v).dtype, np.number)]


def _fmt_cell(v):
    """Format one cell for the table viewer: tidy floats, plain ints, blank None."""
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v: # NaN
            return ""
        return f"{v:.6g}"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (np.floating,)):
        return f"{float(v):.6g}"
    s = str(v)
    # CSV values arrive as strings, prettify if they're numeric
    try:
        f = float(s)
        return f"{f:.6g}" if ("." in s or "e" in s.lower()) else s
    except ValueError:
        return s


def load_table(path, start=0, limit=1000):
    """Read a *window* of rows for the table viewer without loading a huge file into memory.
    Returns dict(columns, rows[list of formatted-str tuples], numeric[set of numeric cols],
    total[int or None], dtypes[dict]). Parquet is read via streaming batches; CSV/gz via a line window."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    start = max(0, int(start)); limit = max(1, int(limit)); end = start + limit

    if path.endswith(".parquet"):
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        total = pf.metadata.num_rows
        schema = pf.schema_arrow
        cols = list(schema.names)
        dtypes = {schema.field(i).name: str(schema.field(i).type) for i in range(len(cols))}
        numeric = {c for c in cols if any(k in dtypes[c] for k in ("int", "float", "double", "decimal"))}
        rows = []; n = 0
        for batch in pf.iter_batches(batch_size=8192):
            d = batch.to_pydict(); bn = len(next(iter(d.values())))
            lo = max(0, start - n); hi = min(bn, end - n)
            for r in range(lo, hi):
                rows.append(tuple(_fmt_cell(d[c][r]) for c in cols))
            n += bn
            if n >= end:
                break
    else: # csv / csv.gz
        import csv
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", newline="") as fh:
            rd = csv.reader(fh)
            cols = next(rd, [])
            rows = []
            for i, row in enumerate(rd):
                if i < start:
                    continue
                if i >= end:
                    break
                rows.append(tuple(_fmt_cell(v) for v in row))
        total = None # unknown without a full scan
        # infer numeric columns from the sampled window
        numeric = set()
        for j, c in enumerate(cols):
            vals = [r[j] for r in rows[:50] if j < len(r) and r[j] != ""]
            if vals and all(_is_num(v) for v in vals):
                numeric.add(c)
        dtypes = {c: ("num" if c in numeric else "str") for c in cols}
    return dict(columns=cols, rows=rows, numeric=numeric, total=total, dtypes=dtypes)


def _is_num(s):
    try:
        float(s); return True
    except (ValueError, TypeError):
        return False


def column_stats(data, col):
    """Return a formatted multi-line stats string for one column."""
    v = np.asarray(data[col], dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return f"{col}: (no finite values)"
    p = np.percentile(v, [1, 5, 25, 50, 75, 95, 99])
    return (f"{col}\n"
            f" n={v.size:,} mean={v.mean():.4g} std={v.std():.4g}\n"
            f" min={v.min():.4g} max={v.max():.4g}\n"
            f" p1={p[0]:.4g} p5={p[1]:.4g} p25={p[2]:.4g} median={p[3]:.4g}"
            f" p75={p[4]:.4g} p95={p[5]:.4g} p99={p[6]:.4g}")


# ------------------------------------------------------------------ figures
def _msg_fig(msg):
    fig = Figure(figsize=(7, 4.5), dpi=100); ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, msg, ha="center", va="center", wrap=True, fontsize=11)
    ax.axis("off"); return fig


def make_figure(kind, data, xcol=None, ycol=None, bins=60, sample=120_000, seed=0):
    """Build a Figure for the requested plot kind. Never raises for bad selections -- returns a
    message figure instead, so the GUI can't crash on a user misclick."""
    if not data:
        return _msg_fig("No dataset loaded.")
    n = len(next(iter(data.values())))
    rng = np.random.default_rng(seed)

    def col(c):
        return np.asarray(data[c], dtype=float)

    fig = Figure(figsize=(8, 5), dpi=100); ax = fig.add_subplot(111)

    if kind == "Histogram":
        if not xcol or xcol not in data:
            return _msg_fig("Pick a column for the histogram.")
        v = col(xcol); v = v[np.isfinite(v)]
        ax.hist(v, bins=bins, color="#2a6f97", edgecolor="white", linewidth=0.3)
        ax.set_xlabel(xcol); ax.set_ylabel("count"); ax.set_title(f"Distribution of {xcol} (n={v.size:,})")
        ax.grid(alpha=0.3)

    elif kind == "Scatter":
        if not (xcol and ycol) or xcol not in data or ycol not in data:
            return _msg_fig("Pick X and Y columns for the scatter plot.")
        idx = rng.choice(n, min(sample, n), replace=False) if n > sample else slice(None)
        x, y = col(xcol)[idx], col(ycol)[idx]
        ax.scatter(x, y, s=4, alpha=0.25, color="#bc4749", linewidths=0)
        ax.set_xlabel(xcol); ax.set_ylabel(ycol)
        shown = min(sample, n)
        ax.set_title(f"{ycol} vs {xcol} ({shown:,} of {n:,} pts)")
        ax.grid(alpha=0.3)

    elif kind == "Density (hexbin)":
        if not (xcol and ycol) or xcol not in data or ycol not in data:
            return _msg_fig("Pick X and Y columns for the density plot.")
        x, y = col(xcol), col(ycol); m = np.isfinite(x) & np.isfinite(y)
        hb = ax.hexbin(x[m], y[m], gridsize=60, cmap="viridis", mincnt=1)
        fig.colorbar(hb, ax=ax, label="count")
        ax.set_xlabel(xcol); ax.set_ylabel(ycol); ax.set_title(f"Density: {ycol} vs {xcol} (n={m.sum():,})")

    elif kind == "Trajectories":
        need = {"flight_id", "t", "z"}
        if not need.issubset(data):
            return _msg_fig("Trajectory plot needs a time-series dataset\n(columns flight_id, t, z).")
        fid = col("flight_id"); t = col("t"); z = col("z")
        x = col("x") if "x" in data else None
        uids = np.unique(fid)
        pick = rng.choice(uids, min(40, uids.size), replace=False)
        for u in pick:
            m = fid == u
            ax.plot(t[m], z[m], lw=0.7, alpha=0.6)
        ax.set_xlabel("t (s)"); ax.set_ylabel("altitude z (m)")
        ax.set_title(f"Altitude traces, {len(pick)} of {uids.size:,} flights")
        ax.grid(alpha=0.3)

    elif kind == "Correlation heatmap":
        cols = [c for c in numeric_cols(data) if c != "flight_id"]
        if len(cols) < 2:
            return _msg_fig("Need >=2 numeric columns for a correlation heatmap.")
        M = np.vstack([col(c) for c in cols])
        finite = np.all(np.isfinite(M), axis=0)
        C = np.corrcoef(M[:, finite])
        im = ax.imshow(C, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=90, fontsize=7)
        ax.set_yticks(range(len(cols))); ax.set_yticklabels(cols, fontsize=7)
        fig.colorbar(im, ax=ax, label="Pearson r")
        ax.set_title("Correlation matrix")
    else:
        return _msg_fig(f"Unknown plot kind: {kind}")

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    # headless self-test over whatever sample datasets exist
    import glob, matplotlib
    matplotlib.use("Agg")
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "datasets", "_plots_selftest"), exist_ok=True)
    for path in glob.glob(os.path.join(here, "datasets", "*.parquet")):
        data, cols, ntot, nload = load_dataset(path, max_load_rows=300_000)
        print(f"{os.path.basename(path)}: {ntot:,} rows ({nload:,} loaded), cols={len(cols)}")
        base = os.path.splitext(os.path.basename(path))[0]
        tests = [("Histogram", "apogee_m" if "apogee_m" in cols else cols[1], None),
                 ("Scatter", "wind_ms" if "wind_ms" in cols else cols[1], cols[-1]),
                 ("Density (hexbin)", "wind_ms" if "wind_ms" in cols else cols[1], cols[-1]),
                 ("Trajectories", None, None),
                 ("Correlation heatmap", None, None)]
        for kind, x, y in tests:
            fig = make_figure(kind, data, xcol=x, ycol=y)
            fig.savefig(os.path.join(here, "datasets", "_plots_selftest",
                                     f"{base}_{kind.split()[0]}.png"), dpi=90)
        print(" plotted:", ", ".join(k for k, _, _ in tests))
    print("analysis self-test OK")
