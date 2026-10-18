#!/usr/bin/env python3
"""
GTR70E WYVERN (fin control), Simulation & Dataset Suite.

Rebuilt from the TVC-era suite for the fin-controlled airframe. Every flight in every tab is
wf_flightsim.simulate() on a wf_core vehicle, so the GUI cannot drift from the engines.

Tabs
  1. Datasets            Monte-Carlo outcomes / 200 Hz traces over a field envelope with build
                         dispersions, process pool, progress, cancel (engine.py, datagen.py)
  2. Plots & Analysis    histogram / scatter / hexbin / trajectories / landing map / authority vs
                         wind / correlation heatmap on any dataset
  3. Data Viewer         virtualized table, click-to-sort
  4. PID Tuner           kp, ki, kd, q_ref, schedule clamp, deflection limit against a gust case,
                         live redraw, grid-search auto-tune, fc_config.h snippet
  5. Flight Computer SIL the manoeuvre replayed through the real firmware code (controller.h),
                         state timeline, emulated ground-station lines, save as a host recording
  6. Authority Manoeuvre doublet + attitude-step programme: nominal response and Monte-Carlo spread
  7. Fin Authority / SQ1 authority matrix, stabilizer span x offset trade, planform trade (plots
                         from wf_fin_authority / wf_stabilizer / wf_stabilizer_planform_trade)
  8. Wind Tunnel Bench   Phase A sweep on two TAL221 cells through the NAU7802 chain, profile
                         comparison, raw vs calibrated
  9. Static Motor Tester .eng curves on the motor stand through the HX711 chain
 10. Super Combined      live N-flight run: apogee, landing scatter, tilt, authority fits
 11. Project Engines     one-click runs of every wf_*.py and the SimScale package generator
 12. About

Launch: python3 run_gui.py   (macOS: Homebrew python3 with Tk 8.6)
"""
import os, sys, time, threading, queue, subprocess, json, math, glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
ROOT = os.path.dirname(SIM)
for p in (HERE, SIM):
    if p not in sys.path: sys.path.insert(0, p)
import engine as E, datagen, analysis, bench, sil          # noqa: E402
import wf_core as C, wf_flightsim as F                       # noqa: E402

DEFAULT_OUT = os.path.join(HERE, "datasets")
ENGINES = [
    ("Canonical numbers (wf_core --report)", ["wf_core.py", "--report"]),
    ("Flight sim + manoeuvre + Monte Carlo", ["wf_flightsim.py"]),
    ("Flight sim, re-tune gains", ["wf_flightsim.py", "--retune"]),
    ("Fin authority matrix (RQ1, RQ2)", ["wf_fin_authority.py"]),
    ("Stabilizer span x offset (SQ1)", ["wf_stabilizer.py"]),
    ("Stabilizer planform trade", ["wf_stabilizer_planform_trade.py"]),
    ("Ejection bypass", ["wf_bypass.py"]),
    ("Battery budget", ["wf_power.py"]),
    ("LoRa link budget", ["wf_link_budget.py"]),
    ("2D airfoil polars (vortex panel)", [os.path.join("CFD", "run_airfoil_cfd.py")]),
    ("SimScale CFD package (STEP/STL + setup)", [os.path.join("CFD", "simscale", "gen_simscale.py")]),
]
ENVELOPE_FIELDS = [
    ("wind_ms", "Wind at 10 m [m/s]"), ("wind_dir_deg", "Wind bearing [deg]"), ("turb_ms", "Turbulence [m/s rms]"),
    ("gust_ms", "1-cos gust [m/s]"), ("temp_C", "Temperature [C]"), ("pressure_mbar", "Pressure [mbar]"),
    ("site_alt_m", "Site elevation [m]"), ("launch_tilt_deg", "Rod angle [deg]"),
]
GRID_BG, GRID_HEAD_BG, GRID_LINE, GRID_FG = "#141414", "#000000", "#ffffff", "#ffffff"


class GridTable(ttk.Frame):
    """Virtualized dark table drawn on a Canvas (only on-screen rows are rendered)."""
    ROWH, PAD, ROW_LINE, COL_LINE = 28, 10, 2, 1

    def __init__(self, master, on_sort=None):
        super().__init__(master)
        self.on_sort = on_sort
        self.cols, self.rows, self.numeric = [], [], set()
        self.colw, self.colx, self.total_w = [], [], 0
        self.sort_col, self.sort_rev = None, False
        self._top = 0; self._xoff = 0
        try: self._font = tkfont.nametofont("TkDefaultFont").copy()
        except Exception: self._font = tkfont.Font(family="TkDefaultFont", size=10)
        self.header = tk.Canvas(self, height=self.ROWH, bg=GRID_HEAD_BG, highlightthickness=0, bd=0)
        self.body = tk.Canvas(self, bg=GRID_BG, highlightthickness=0, bd=0)
        self.vs = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.hs = ttk.Scrollbar(self, orient="horizontal", command=self._xview)
        self.header.grid(row=0, column=0, sticky="ew"); self.body.grid(row=1, column=0, sticky="nsew")
        self.vs.grid(row=1, column=1, sticky="ns"); self.hs.grid(row=2, column=0, sticky="ew")
        self.rowconfigure(1, weight=1); self.columnconfigure(0, weight=1)
        self.body.bind("<Configure>", lambda e: self._redraw())
        self.body.bind("<MouseWheel>", lambda e: self._wheel(-1 if e.delta > 0 else 1))
        self.body.bind("<Button-4>", lambda e: self._wheel(-3)); self.body.bind("<Button-5>", lambda e: self._wheel(3))
        self.header.bind("<Button-1>", self._on_header_click)

    def set_data(self, cols, rows, numeric, sort_col=None, sort_rev=False):
        self.cols, self.rows, self.numeric = list(cols), list(rows), set(numeric or ())
        self.sort_col, self.sort_rev = sort_col, sort_rev; self._top = 0
        m = self._font.measure; self.colw = []
        for j, c in enumerate(self.cols):
            w = m(str(c)) + 24
            for r in self.rows[:60]:
                if j < len(r): w = max(w, m(str(r[j])))
            self.colw.append(min(w + 2 * self.PAD, 320))
        self.colx = [0]
        for w in self.colw: self.colx.append(self.colx[-1] + w)
        self.total_w = self.colx[-1] if self.colx else 0
        self._redraw()

    def _nvis(self): return max(1, max(1, self.body.winfo_height()) // self.ROWH + 2)
    def _max_top(self): return max(0, len(self.rows) - (self._nvis() - 1))
    def _yview(self, *a):
        n = len(self.rows)
        if not n: return
        if a[0] == "moveto": self._top = int(float(a[1]) * n)
        elif a[0] == "scroll": self._top += int(a[1]) * (self._nvis() - 2 if a[2] == "pages" else 1)
        self._top = max(0, min(self._top, self._max_top())); self._redraw()
    def _xview(self, *a):
        span = max(0, self.total_w - max(1, self.body.winfo_width()))
        if a[0] == "moveto": self._xoff = int(float(a[1]) * span)
        elif a[0] == "scroll": self._xoff += int(a[1]) * 40
        self._xoff = max(0, min(self._xoff, span)); self._redraw()
    def _wheel(self, s): self._top = max(0, min(self._top + s, self._max_top())); self._redraw()
    def _on_header_click(self, e):
        x = e.x + self._xoff
        for j in range(len(self.cols)):
            if self.colx[j] <= x < self.colx[j + 1]:
                if self.on_sort: self.on_sort(self.cols[j])
                break

    def _redraw(self):
        self.header.delete("all"); self.body.delete("all")
        if not self.cols: return
        vw = max(1, self.body.winfo_width()); n = len(self.rows)
        self.vs.set(self._top / n if n else 0, min(1.0, (self._top + self._nvis() - 1) / n) if n else 1)
        if self.total_w: self.hs.set(self._xoff / self.total_w, min(1.0, (self._xoff + vw) / self.total_w))
        for j, c in enumerate(self.cols):
            x0 = self.colx[j] - self._xoff
            if x0 > vw or self.colx[j + 1] - self._xoff < 0: continue
            self.header.create_line(x0, 0, x0, self.ROWH, fill=GRID_LINE, width=self.COL_LINE)
            arrow = (" ▲" if not self.sort_rev else " ▼") if c == self.sort_col else ""
            self.header.create_text(x0 + self.PAD, self.ROWH // 2, anchor="w", text=str(c) + arrow, fill=GRID_FG, font=self._font)
        self.header.create_line(0, self.ROWH - 1, vw, self.ROWH - 1, fill=GRID_LINE, width=self.ROW_LINE)
        end = min(n, self._top + self._nvis()); right = min(vw, self.total_w - self._xoff)
        for vi, ri in enumerate(range(self._top, end)):
            y0 = vi * self.ROWH; r = self.rows[ri]
            self.body.create_line(0, y0, right, y0, fill=GRID_LINE, width=self.ROW_LINE)
            for j, c in enumerate(self.cols):
                x0 = self.colx[j] - self._xoff
                if x0 > vw or self.colx[j + 1] - self._xoff < 0: continue
                val = str(r[j]) if j < len(r) else ""
                if c in self.numeric:
                    self.body.create_text(self.colx[j + 1] - self._xoff - self.PAD, y0 + self.ROWH // 2, anchor="e", text=val, fill=GRID_FG, font=self._font)
                else:
                    self.body.create_text(x0 + self.PAD, y0 + self.ROWH // 2, anchor="w", text=val, fill=GRID_FG, font=self._font)
        h = (end - self._top) * self.ROWH
        for j in range(len(self.cols) + 1):
            x0 = self.colx[j] - self._xoff
            if -1 <= x0 <= vw + 1: self.body.create_line(x0, 0, x0, h, fill=GRID_LINE, width=self.COL_LINE)
        self.body.create_line(0, h, right, h, fill=GRID_LINE, width=self.ROW_LINE)


def embed(holder, fig, toolbar=True):
    for w in holder.winfo_children(): w.destroy()
    cv = FigureCanvasTkAgg(fig, master=holder); cv.draw()
    if toolbar:
        tb = NavigationToolbar2Tk(cv, holder, pack_toolbar=False); tb.update(); tb.pack(side="top", fill="x")
    cv.get_tk_widget().pack(side="top", fill="both", expand=True)
    return cv


class Suite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GTR70E WYVERN (fin control): Simulation & Dataset Suite")
        try:
            st = ttk.Style(self)
            if tuple(int(x) for x in self.tk.call("info", "patchlevel").split(".")[:2]) < (8, 6) and "clam" in st.theme_names():
                st.theme_use("clam")
        except Exception: pass
        self.q = queue.Queue(); self.cancel_evt = threading.Event()
        self.dataset = None; self.last_output = None
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=6, pady=6); self.nb = nb
        for b in (self._tab_datasets, self._tab_plots, self._tab_viewer, self._tab_pid, self._tab_sil, self._tab_man,
                  self._tab_authority, self._tab_tunnel, self._tab_motor, self._tab_combined, self._tab_engines, self._tab_about):
            b(nb)
        self.update_idletasks()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        try: self.state("zoomed")
        except Exception: pass
        self._fs = False
        self.bind("<F11>", lambda e: self._set_fs(not self._fs)); self.bind("<Escape>", lambda e: self._set_fs(False))
        self.after(120, self._drain)

    def _set_fs(self, on):
        self._fs = on
        try: self.attributes("-fullscreen", on)
        except Exception: pass

    def bg(self, fn, tag):
        """Run fn() in a thread; its result goes to the queue as (tag, result)."""
        def run():
            try: self.q.put((tag, fn()))
            except Exception as e:
                import traceback; self.q.put(("error", f"{tag}: {e!r}\n{traceback.format_exc()[-1500:]}"))
        threading.Thread(target=run, daemon=True).start()

    def _drain(self):
        try:
            while True:
                tag, val = self.q.get_nowait()
                h = getattr(self, "_on_" + tag, None)
                if h: h(val)
                elif tag == "error": messagebox.showerror("WYVERN suite", str(val)[:3000])
        except queue.Empty: pass
        self.after(100, self._drain)

    # =================================================================== 1 datasets
    def _tab_datasets(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Datasets")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Monte-Carlo flight datasets", font=("", 12, "bold")).pack(anchor="w")
        pr = ttk.Frame(left); pr.pack(fill="x", pady=4)
        ttk.Label(pr, text="Preset").pack(side="left")
        self.ds_preset = tk.StringVar(value="Typical field")
        cb = ttk.Combobox(pr, textvariable=self.ds_preset, values=list(E.PRESETS), state="readonly", width=20)
        cb.pack(side="left", padx=6); cb.bind("<<ComboboxSelected>>", lambda e: self._ds_apply_preset())
        env = ttk.LabelFrame(left, text="Envelope (uniform lo..hi)"); env.pack(fill="x", pady=4)
        self.ds_env = {}
        for i, (k, lbl) in enumerate(ENVELOPE_FIELDS):
            ttk.Label(env, text=lbl).grid(row=i, column=0, sticky="w")
            lo, hi = tk.StringVar(), tk.StringVar()
            ttk.Entry(env, textvariable=lo, width=8).grid(row=i, column=1, padx=2)
            ttk.Entry(env, textvariable=hi, width=8).grid(row=i, column=2, padx=2)
            self.ds_env[k] = (lo, hi)
        self._ds_apply_preset()
        run = ttk.LabelFrame(left, text="Run"); run.pack(fill="x", pady=4)
        self.ds_vars = {}
        for i, (k, lbl, v) in enumerate((("n", "Flights", "500"), ("seed", "Seed", "0"),
                                         ("workers", "Workers", str(max(1, (os.cpu_count() or 2) - 1))),
                                         ("dt", "dt [s]", "0.002"), ("stride", "Trace stride", "4"))):
            ttk.Label(run, text=lbl).grid(row=i, column=0, sticky="w")
            self.ds_vars[k] = tk.StringVar(value=v); ttk.Entry(run, textvariable=self.ds_vars[k], width=10).grid(row=i, column=1)
        self.ds_kind = tk.StringVar(value="outcomes")
        kf = ttk.Frame(run); kf.grid(row=5, column=0, columnspan=2, sticky="w")
        for k in ("outcomes", "traces", "both"): ttk.Radiobutton(kf, text=k, value=k, variable=self.ds_kind).pack(side="left")
        self.ds_locked = tk.BooleanVar(value=False)
        ttk.Checkbutton(run, text="Fins locked (passive baseline)", variable=self.ds_locked).grid(row=6, column=0, columnspan=2, sticky="w")
        self.ds_fmt = tk.StringVar(value="csv")
        ff = ttk.Frame(run); ff.grid(row=7, column=0, columnspan=2, sticky="w")
        for k in ("csv", "parquet"): ttk.Radiobutton(ff, text=k, value=k, variable=self.ds_fmt).pack(side="left")
        self.ds_out = tk.StringVar(value=os.path.join(DEFAULT_OUT, "run.csv"))
        of = ttk.Frame(left); of.pack(fill="x", pady=2)
        ttk.Entry(of, textvariable=self.ds_out, width=34).pack(side="left")
        ttk.Button(of, text="…", width=3, command=lambda: self.ds_out.set(filedialog.asksaveasfilename(initialdir=DEFAULT_OUT, defaultextension=".csv") or self.ds_out.get())).pack(side="left")
        bf = ttk.Frame(left); bf.pack(fill="x", pady=4)
        self.ds_btn = ttk.Button(bf, text="Generate ▶", command=self._ds_go); self.ds_btn.pack(side="left")
        ttk.Button(bf, text="Cancel", command=self.cancel_evt.set).pack(side="left", padx=6)
        ttk.Button(bf, text="Open folder", command=lambda: self._open(os.path.dirname(self.ds_out.get()))).pack(side="left")
        self.ds_prog = ttk.Progressbar(left, length=300); self.ds_prog.pack(fill="x", pady=4)
        self.ds_status = ttk.Label(left, text=""); self.ds_status.pack(anchor="w")
        self.ds_log = tk.Text(f, wrap="word"); self.ds_log.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        self.ds_log.insert("end", "Each flight is wf_flightsim on a dispersed vehicle (mass, CG, drag, impulse, fin rigging, "
                           "servo speed) in a sampled field condition, with the firmware control rule and the authority "
                           "manoeuvre. About 0.4 s per flight per core at dt = 0.002 s.\n\nDispersions (1 sd):\n"
                           + "\n".join(f"  {k}: {v}" for k, v in E.DISPERSION.items()) + "\n\n")

    def _ds_apply_preset(self):
        p = E.PRESETS[self.ds_preset.get()]
        for k, (lo, hi) in self.ds_env.items(): lo.set(str(p[k][0])); hi.set(str(p[k][1]))

    def _ds_go(self):
        try:
            env = {k: (float(lo.get()), float(hi.get())) for k, (lo, hi) in self.ds_env.items()}
            n = int(self.ds_vars["n"].get()); seed = int(self.ds_vars["seed"].get()); wk = int(self.ds_vars["workers"].get())
            dt = float(self.ds_vars["dt"].get()); stride = int(self.ds_vars["stride"].get())
        except ValueError:
            messagebox.showerror("Datasets", "Envelope and run fields must be numbers."); return
        self.cancel_evt.clear(); self.ds_btn.config(state="disabled"); self.ds_prog.config(maximum=n, value=0)
        out = self.ds_out.get(); kind = self.ds_kind.get(); locked = self.ds_locked.get(); fmt = self.ds_fmt.get()
        def prog(d, tot, rate): self.q.put(("ds_prog", (d, tot, rate)))
        def log(s): self.q.put(("ds_log", s))
        self.bg(lambda: datagen.generate(kind, n, out, seed, env, wk, dt, stride, not locked, fmt, prog, self.cancel_evt, log), "ds_done")

    def _on_ds_prog(self, v):
        d, tot, rate = v; self.ds_prog.config(value=d)
        self.ds_status.config(text=f"{d}/{tot} flights, {rate:.1f}/s, eta {(tot - d) / max(rate, 1e-6):.0f} s")
    def _on_ds_log(self, s): self.ds_log.insert("end", s + "\n"); self.ds_log.see("end")
    def _on_ds_done(self, paths):
        self.ds_btn.config(state="normal")
        if paths: self.last_output = paths[0]; self.ds_log.insert("end", "done: " + ", ".join(paths) + "\n")

    def _open(self, path):
        try: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
        except Exception: pass

    # =================================================================== 2 plots
    def _tab_plots(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Plots & Analysis")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Load dataset…", command=lambda: self._load(filedialog.askopenfilename(initialdir=DEFAULT_OUT))).pack(side="left")
        ttk.Button(bar, text="Load last generated", command=lambda: self._load(self.last_output)).pack(side="left", padx=6)
        self.pl_lbl = ttk.Label(bar, text="(no dataset loaded)"); self.pl_lbl.pack(side="left", padx=10)
        ctl = ttk.Frame(f); ctl.pack(fill="x", padx=8)
        self.pl_kind = tk.StringVar(value=analysis.PLOT_KINDS[0])
        ttk.Combobox(ctl, textvariable=self.pl_kind, values=analysis.PLOT_KINDS, state="readonly", width=20).pack(side="left")
        ttk.Label(ctl, text="X").pack(side="left", padx=(8, 2)); self.pl_x = ttk.Combobox(ctl, width=20, state="readonly"); self.pl_x.pack(side="left")
        ttk.Label(ctl, text="Y").pack(side="left", padx=(8, 2)); self.pl_y = ttk.Combobox(ctl, width=20, state="readonly"); self.pl_y.pack(side="left")
        self.pl_bins = tk.StringVar(value="50"); ttk.Label(ctl, text="bins").pack(side="left", padx=(8, 2))
        ttk.Entry(ctl, textvariable=self.pl_bins, width=5).pack(side="left")
        ttk.Button(ctl, text="Plot", command=self._plot).pack(side="left", padx=8)
        ttk.Button(ctl, text="Column stats", command=self._stats).pack(side="left")
        body = ttk.Frame(f); body.pack(fill="both", expand=True, padx=8, pady=4)
        self.pl_holder = ttk.Frame(body); self.pl_holder.pack(side="left", fill="both", expand=True)
        self.pl_stats = tk.Text(body, width=40, wrap="word"); self.pl_stats.pack(side="right", fill="y")

    def _load(self, path):
        if not path or not os.path.exists(path):
            messagebox.showinfo("Load", "No dataset file."); return
        self.pl_lbl.config(text="loading…")
        self.bg(lambda: (path,) + analysis.load_dataset(path), "loaded")

    def _on_loaded(self, v):
        path, data, cols, ntot, nload = v; self.dataset = data
        nums = analysis.numeric_cols(data); self.pl_x.config(values=nums); self.pl_y.config(values=nums)
        if nums: self.pl_x.set("wind_ms" if "wind_ms" in nums else nums[0]); self.pl_y.set("apogee_m" if "apogee_m" in nums else nums[-1])
        self.pl_lbl.config(text=f"{os.path.basename(path)}: {ntot:,} rows ({nload:,} loaded), {len(cols)} columns")

    def _plot(self):
        if not self.dataset: messagebox.showinfo("Plot", "Load a dataset first."); return
        try: bins = int(self.pl_bins.get())
        except ValueError: bins = 50
        embed(self.pl_holder, analysis.make_figure(self.pl_kind.get(), self.dataset, self.pl_x.get() or None, self.pl_y.get() or None, bins))

    def _stats(self):
        if not self.dataset or not self.pl_x.get(): return
        self.pl_stats.delete("1.0", "end"); self.pl_stats.insert("end", analysis.column_stats(self.dataset, self.pl_x.get()))

    # =================================================================== 3 viewer
    def _tab_viewer(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Data Viewer")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        self.vw_path = None
        ttk.Button(bar, text="Load file…", command=lambda: self._vw_load(filedialog.askopenfilename(initialdir=DEFAULT_OUT))).pack(side="left")
        ttk.Button(bar, text="Load last generated", command=lambda: self._vw_load(self.last_output)).pack(side="left", padx=6)
        ttk.Label(bar, text="Start row").pack(side="left", padx=(10, 2)); self.vw_start = tk.StringVar(value="0")
        ttk.Entry(bar, textvariable=self.vw_start, width=8).pack(side="left")
        ttk.Label(bar, text="Rows").pack(side="left", padx=(8, 2)); self.vw_lim = tk.StringVar(value="10000")
        ttk.Entry(bar, textvariable=self.vw_lim, width=8).pack(side="left")
        ttk.Button(bar, text="Reload", command=lambda: self._vw_load(self.vw_path)).pack(side="left", padx=6)
        self.vw_info = ttk.Label(bar, text=""); self.vw_info.pack(side="left", padx=10)
        self.vw_table = GridTable(f, on_sort=self._vw_sort); self.vw_table.pack(fill="both", expand=True, padx=8, pady=4)
        self.vw_rows, self.vw_cols, self.vw_sorted = [], [], (None, False)

    def _vw_load(self, path):
        if not path or not os.path.exists(path): return
        self.vw_path = path
        s, l = int(self.vw_start.get() or 0), int(self.vw_lim.get() or 10000)
        self.bg(lambda: analysis.load_table(path, start=s, limit=l), "vw")

    def _on_vw(self, r):
        self.vw_cols, self.vw_rows = r["columns"], r["rows"]
        self.vw_table.set_data(r["columns"], r["rows"], r.get("numeric", set()))
        self.vw_info.config(text=f"{os.path.basename(self.vw_path)}: {len(self.vw_rows):,} rows shown" + (f" of {r['total']:,}" if r.get("total") else ""))

    def _vw_sort(self, col):
        j = self.vw_cols.index(col); prev, rev = self.vw_sorted; rev = (not rev) if prev == col else False
        def key(r):
            try: return (0, float(r[j]))
            except (ValueError, TypeError, IndexError): return (1, str(r[j]) if j < len(r) else "")
        self.vw_rows.sort(key=key, reverse=rev); self.vw_sorted = (col, rev)
        self.vw_table.set_data(self.vw_cols, self.vw_rows, self.vw_table.numeric, col, rev)

    # =================================================================== 4 PID tuner
    def _tab_pid(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="PID Tuner")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Fin-control tilt loop", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="delta = S(q) (kp th + ki int th + kd w),  S = clamp(q_ref / q)", foreground="#555").pack(anchor="w")
        self.pid = {}; G = F.GAINS_FLIGHT
        def slider(parent, k, lbl, lo, hi, init):
            r = ttk.Frame(parent); r.pack(fill="x", pady=1)
            ttk.Label(r, text=lbl, width=16).pack(side="left")
            v = tk.DoubleVar(value=init); l = ttk.Label(r, text=f"{init:g}", width=7); l.pack(side="right")
            ttk.Scale(r, from_=lo, to=hi, variable=v, orient="horizontal",
                      command=lambda _x, l=l, v=v: (l.config(text=f"{v.get():.3g}"), setattr(self, "_pid_dirty", time.time()))).pack(side="left", fill="x", expand=True)
            self.pid[k] = v
        g = ttk.LabelFrame(left, text="Gains (firmware: fc_config.h)"); g.pack(fill="x", pady=4)
        slider(g, "kp", "kp", 0, 10, G["kp"]); slider(g, "ki", "ki", 0, 4, G["ki"]); slider(g, "kd", "kd", 0, 2, G["kd"])
        slider(g, "q_ref", "q_ref [Pa]", 300, 4000, G["q_ref"]); slider(g, "k_min", "schedule min", 0.05, 1, G["k_min"])
        slider(g, "k_max", "schedule max", 1, 8, G["k_max"]); slider(g, "defl", "deflection limit [deg]", 5, 20, C.CFIN["defl_max_deg"])
        c = ttk.LabelFrame(left, text="Case"); c.pack(fill="x", pady=4)
        slider(c, "wind", "wind [m/s]", 0, 9, 4.0); slider(c, "gust", "gust [m/s]", 0, 8, 4.0)
        slider(c, "turb", "turbulence [m/s]", 0, 2, 1.0); slider(c, "tilt", "rod angle [deg]", 0, 8, 0.0)
        slider(c, "seed", "seed", 1, 50, 1)
        self.pid_live = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Live update", variable=self.pid_live).pack(anchor="w")
        bf = ttk.Frame(left); bf.pack(fill="x", pady=3)
        ttk.Button(bf, text="Reset to firmware", command=self._pid_reset).pack(side="left")
        ttk.Button(bf, text="Recompute", command=self._pid_run).pack(side="left", padx=4)
        self.pid_tune_btn = ttk.Button(bf, text="Auto-tune", command=self._pid_tune); self.pid_tune_btn.pack(side="left")
        self.pid_txt = tk.Text(left, width=40, height=14, wrap="word"); self.pid_txt.pack(fill="x", pady=4)
        self.pid_holder = ttk.Frame(f); self.pid_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self._pid_dirty = time.time(); self._pid_busy = False; self._pid_seen = 0
        self.after(300, self._pid_tick)

    def _pid_reset(self):
        G = F.GAINS_FLIGHT
        for k in ("kp", "ki", "kd", "q_ref", "k_min", "k_max"): self.pid[k].set(G[k])
        self.pid["defl"].set(C.CFIN["defl_max_deg"]); self._pid_dirty = time.time()

    def _pid_tick(self):
        if self.pid_live.get() and not self._pid_busy and self._pid_dirty > self._pid_seen and time.time() - self._pid_dirty > 0.25:
            self._pid_run()
        self.after(150, self._pid_tick)

    def _pid_gains(self): return {k: self.pid[k].get() for k in ("kp", "ki", "kd", "q_ref", "k_min", "k_max")}

    def _pid_run(self):
        self._pid_busy = True; self._pid_seen = time.time()
        g = self._pid_gains(); v = {k: self.pid[k].get() for k in ("defl", "wind", "gust", "turb", "tilt", "seed")}
        def job():
            veh = F.Vehicle()
            kw = dict(wind=v["wind"], gust=v["gust"], turb=v["turb"], seed=int(v["seed"]), launch_tilt_deg=v["tilt"], dt=0.001)
            r, H = F.simulate(veh, gains=g, defl_max_deg=v["defl"], **kw)
            r0, H0 = F.simulate(veh, gains=F.GAINS_FLIGHT, **kw)
            rl, HL = F.simulate(veh, control=False, **kw)
            return g, v, (r, H), (r0, H0), (rl, HL)
        self.bg(job, "pid")

    def _on_pid(self, val):
        g, v, (r, H), (r0, H0), (rl, HL) = val; self._pid_busy = False
        fig = Figure(figsize=(9, 7), dpi=100); a1, a2, a3 = fig.add_subplot(311), fig.add_subplot(312), fig.add_subplot(313)
        a1.plot(H["t"], H["th"], "#2a6f97", lw=1.5, label="your gains"); a1.plot(H0["t"], H0["th"], "#999", ls="--", lw=1, label="firmware gains")
        a1.plot(HL["t"], HL["th"], "#bc4749", lw=0.8, alpha=0.7, label="fins locked")
        a1.set_ylabel("tilt (deg)"); a1.legend(fontsize=8); a1.grid(alpha=0.3)
        a1.set_title(f"kp {g['kp']:.2f} ki {g['ki']:.2f} kd {g['kd']:.2f}  q_ref {g['q_ref']:.0f}  ({v['wind']:.1f} m/s wind, {v['gust']:.1f} m/s gust at 1.2 s)")
        a2.plot(H["t"], H["dl"], "#2a6f97", lw=1.0); a2.plot(H0["t"], H0["dl"], "#999", ls="--", lw=0.8)
        a2.axhline(v["defl"], c="#bc4749", ls=":", lw=0.8); a2.axhline(-v["defl"], c="#bc4749", ls=":", lw=0.8)
        a2.set_ylabel("pair deflection (deg)"); a2.grid(alpha=0.3)
        a3.plot(H["t"], H["qbar"], "#386641"); a3b = a3.twinx(); a3b.plot(H["t"], np.array(H["hm"]) * 1000, "#e76f51", lw=0.8)
        a3.set_ylabel("q (Pa)"); a3b.set_ylabel("hinge (mN m)", color="#e76f51"); a3.set_xlabel("t (s)"); a3.grid(alpha=0.3)
        for a in (a1, a2, a3): a.set_xlim(0, min(H["t"][-1], 8))
        fig.tight_layout(); embed(self.pid_holder, fig, toolbar=False)
        self.pid_txt.delete("1.0", "end")
        self.pid_txt.insert("end", f"tilt rms {r['tilt_rms_deg']:.2f} deg (firmware {r0['tilt_rms_deg']:.2f}, locked {rl['tilt_rms_deg']:.2f})\n"
                            f"tilt max {r['tilt_max_deg']:.2f} deg\nservo rate-limited {r['servo_rate_sat_s'] * 1000:.0f} ms\n"
                            f"peak hinge {r['max_hinge_Nm'] * 1000:.1f} mN m (X08 Plus stall ~{F.servo_stall_Nm() * 1000:.0f})\n"
                            f"apogee {r['apogee_m']:.1f} m\n\nfc_config.h:\n#define WYV_KP {g['kp']:.2f}f\n#define WYV_KI {g['ki']:.2f}f\n"
                            f"#define WYV_KD {g['kd']:.2f}f\n#define WYV_Q_REF_PA {g['q_ref']:.0f}.0f\n#define WYV_SCHED_MIN {g['k_min']:.2f}f\n"
                            f"#define WYV_SCHED_MAX {g['k_max']:.2f}f\n")

    def _pid_tune(self):
        self.pid_tune_btn.config(state="disabled"); self.pid_txt.delete("1.0", "end")
        self.pid_txt.insert("end", "grid search over kp x kd x ki (48 flights, ~40 s)…")
        w, gu = self.pid["wind"].get(), self.pid["gust"].get()
        self.bg(lambda: F.tune(F.Vehicle(), wind=w, gust=gu), "tuned")

    def _on_tuned(self, best):
        self.pid_tune_btn.config(state="normal"); score, g, r = best
        for k in ("kp", "ki", "kd"): self.pid[k].set(g[k])
        self._pid_dirty = time.time()

    # =================================================================== 5 SIL
    def _tab_sil(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Flight Computer SIL")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Firmware in the loop", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, justify="left", text="The authority manoeuvre is flown in the simulator and\nreplayed through the flight code (controller.h,\ncompiled for this computer). Both sets of metrics\nare shown side by side.").pack(anchor="w")
        self.sil = {}
        for k, lbl, v in (("wind", "wind [m/s]", "4"), ("gust", "gust [m/s]", "0"), ("turb", "turbulence [m/s]", "0.5"),
                          ("tilt", "rod angle [deg]", "0"), ("seed", "seed", "3")):
            r = ttk.Frame(left); r.pack(fill="x", pady=1); ttk.Label(r, text=lbl, width=22).pack(side="left")
            self.sil[k] = tk.StringVar(value=v); ttk.Entry(r, textvariable=self.sil[k], width=10).pack(side="left")
        bf = ttk.Frame(left); bf.pack(fill="x", pady=4)
        self.sil_btn = ttk.Button(bf, text="Run SIL ▶", command=self._sil_run); self.sil_btn.pack(side="left")
        ttk.Button(bf, text="Save as host recording", command=self._sil_save).pack(side="left", padx=6)
        self.sil_txt = tk.Text(left, width=52, height=16, wrap="none", font=("Menlo", 10)); self.sil_txt.pack(fill="x", pady=4)
        ttk.Label(left, text="Ground-station USB lines (emulated):").pack(anchor="w")
        self.sil_con = tk.Text(left, width=52, height=14, wrap="none", bg="#0b1020", fg="#7CFC98", font=("Menlo", 9))
        self.sil_con.pack(fill="both", expand=True)
        self.sil_holder = ttk.Frame(f); self.sil_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self._sil_lines = []

    def _sil_run(self):
        try: v = {k: float(s.get()) for k, s in self.sil.items()}
        except ValueError: messagebox.showerror("SIL", "numbers only"); return
        self.sil_btn.config(state="disabled"); self.sil_txt.delete("1.0", "end"); self.sil_txt.insert("end", "running (two flights + replay)…")
        self.bg(lambda: sil.run(v["wind"], v["gust"], v["turb"], int(v["seed"]), v["tilt"]), "sil")

    def _on_sil(self, val):
        res, tr, st, lines = val; self.sil_btn.config(state="normal"); self._sil_lines = lines
        t = self.sil_txt; t.delete("1.0", "end")
        t.insert("end", f"{'':22s}{'sim A':>9s}{'fw A':>9s}{'sim B':>9s}{'fw B':>9s}\n")
        def g(ax, src, sect, k):
            d = res[ax][src] or {}
            if src == "sim": d = d.get(sect, {}) or {}
            v = d.get(k); return f"{v:9.3f}" if isinstance(v, (int, float)) and v is not None and v == v else f"{'-':>9s}"
        rows = [("doublet q [Pa]", "doublet", "qbar_Pa", "qbar_d"), ("M_delta/I [1/s2]", "doublet", "b_fit", "b_fit"),
                ("t statistic", "doublet", "t_stat", "b_t"), ("fit / model", "doublet", "b_ratio", "b_ratio"),
                ("step q [Pa]", "step", "qbar_Pa", "qbar_s"), ("step sign", "step", "sign", "step_sign"),
                ("achieved [deg]", "step", "achieved_deg", "achieved_deg"), ("t63 [s]", "step", "t63_s", "t63_s"),
                ("overshoot [%]", "step", "overshoot_pct", "overshoot_pct"), ("fin per deg", "step", "fin_per_deg", "fin_per_deg"),
                ("return t63 [s]", "step", "return63_s", "return63_s")]
        for lbl, sect, ks, kf in rows:
            t.insert("end", f"{lbl:22s}{g('A', 'sim', sect, ks)}{g('A', 'fw', None, kf)}{g('B', 'sim', sect, ks)}{g('B', 'fw', None, kf)}\n")
        if res["A"]["fw"] is None: t.insert("end", "\n(no C++ compiler found: firmware columns empty)\n")
        t.insert("end", f"\napogee {res['A']['apogee']:.1f} m at {res['A']['t_apogee']:.2f} s\n")
        self.sil_con.delete("1.0", "end"); self.sil_con.insert("end", "\n".join(lines[:400]))
        H = tr["A"]; HB = tr["B"]
        fig = Figure(figsize=(9, 7.5), dpi=100); ax = [fig.add_subplot(4, 1, i + 1) for i in range(4)]
        ax[0].plot(H["t"], H["z"], "#2a6f97"); ax[0].set_ylabel("alt (m)")
        a0 = ax[0].twinx(); a0.step(H["t"], st, "#bc4749", lw=0.8, where="post"); a0.set_yticks(range(4, 8)); a0.set_yticklabels(sil.STATES[4:8], fontsize=7)
        ax[1].plot(H["t"], H["th"], "#2a6f97", label="tilt, programme A"); ax[1].plot(H["t"], H["ref"], "#2a6f97", ls=":", lw=1)
        ax[1].plot(HB["t"], HB["th"], "#bc4749", label="tilt, programme B"); ax[1].plot(HB["t"], HB["ref"], "#bc4749", ls=":", lw=1)
        ax[1].set_ylabel("tilt (deg)"); ax[1].legend(fontsize=7)
        ax[2].plot(H["t"], H["dl"], "#2a6f97"); ax[2].plot(H["t"], H["inj"], "#2a6f97", ls=":"); ax[2].plot(HB["t"], HB["dl"], "#bc4749")
        ax[2].set_ylabel("pair defl (deg)")
        ax[3].plot(H["t"], H["qbar"], "#386641"); ax[3].set_ylabel("q (Pa)"); ax[3].set_xlabel("t (s)")
        t0 = F.MAN_T0_AFTER_BURN + C.MOTORS[C.FLIGHT_MOTOR]["tb"]
        for a in ax: a.grid(alpha=0.3); a.axvspan(t0, t0 + 2.6, color="#ffd166", alpha=0.15)
        fig.tight_layout(); embed(self.sil_holder, fig)

    def _sil_save(self):
        if not self._sil_lines: messagebox.showinfo("SIL", "Run the SIL first."); return
        d = filedialog.askdirectory(title="Folder for the recording") or None
        if not d: return
        stem = os.path.join(d, time.strftime("sil_%Y-%m-%d_%H%M%S"))
        sil.save_recording(self._sil_lines, stem)
        messagebox.showinfo("SIL", f"Saved {stem}_[T,M].csv\nOpen with: python3 wyvern_host.py --replay {stem}")

    # =================================================================== 6 manoeuvre
    def _tab_man(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Authority Manoeuvre")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Authority-demonstration programme", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, justify="left", text="t0 = burnout + 0.25 s. Doublets identify M_delta / I by\nleast squares; the 1 deg attitude steps show the loop\nsteering. Same numbers as fc_config.h WYV_MAN_*.").pack(anchor="w")
        self.man = {}
        for k, lbl, v in (("doublet_deg", "doublet amplitude [deg]", F.MAN["doublet_deg"]), ("doublet_half", "doublet half [s]", F.MAN["doublet_half"]),
                          ("step_deg", "step [deg]", F.MAN["step_deg"]), ("hold", "step hold [s]", F.MAN["hold"]), ("rest", "rest [s]", F.MAN["rest"]),
                          ("wind", "wind [m/s]", 4.0), ("turb", "turbulence [m/s]", 0.5), ("n", "Monte-Carlo flights", 40)):
            r = ttk.Frame(left); r.pack(fill="x", pady=1); ttk.Label(r, text=lbl, width=24).pack(side="left")
            self.man[k] = tk.StringVar(value=str(v)); ttk.Entry(r, textvariable=self.man[k], width=8).pack(side="left")
        bf = ttk.Frame(left); bf.pack(fill="x", pady=4)
        self.man_btn = ttk.Button(bf, text="Nominal ▶", command=self._man_run); self.man_btn.pack(side="left")
        self.man_mc_btn = ttk.Button(bf, text="Monte Carlo ▶", command=self._man_mc); self.man_mc_btn.pack(side="left", padx=6)
        self.man_txt = tk.Text(left, width=46, height=22, wrap="word"); self.man_txt.pack(fill="both", expand=True, pady=4)
        self.man_holder = ttk.Frame(f); self.man_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        try:
            pr = json.load(open(os.path.join(SIM, "plots_flight", "maneuver_prediction.json")))
            self.man_txt.insert("end", "Last wf_flightsim prediction:\n" + json.dumps({k: pr[k] for k in ("A", "B")}, indent=1, default=float)[:2500])
        except Exception: pass

    def _man_apply(self):
        for k in ("doublet_deg", "doublet_half", "step_deg", "hold", "rest"): F.MAN[k] = float(self.man[k].get())

    def _man_run(self):
        self._man_apply(); w, tu = float(self.man["wind"].get()), float(self.man["turb"].get())
        self.man_btn.config(state="disabled")
        self.bg(lambda: F.run_maneuver(wind=w, turb=tu), "man")

    def _on_man(self, val):
        out, Hs = val; self.man_btn.config(state="normal")
        import tempfile; p = os.path.join(tempfile.gettempdir(), "wyv_man.png"); F.plot_maneuver(out, Hs, p)
        fig = Figure(figsize=(9, 8), dpi=100); a = fig.add_subplot(111); a.imshow(__import__("matplotlib.image", fromlist=["imread"]).imread(p)); a.axis("off")
        fig.tight_layout(); embed(self.man_holder, fig)
        self.man_txt.delete("1.0", "end"); self.man_txt.insert("end", json.dumps({k: out[k] for k in ("A", "B")}, indent=1, default=lambda x: round(float(x), 4)))

    def _man_mc(self):
        self._man_apply(); n = int(float(self.man["n"].get())); self.man_mc_btn.config(state="disabled")
        self.man_txt.delete("1.0", "end"); self.man_txt.insert("end", f"{n} flights x 2 axes, wind 0-7 m/s…")
        self.bg(lambda: F.maneuver_monte_carlo(n=n), "man_mc")

    def _on_man_mc(self, val):
        summ, rows = val; self.man_mc_btn.config(state="normal")
        fig = Figure(figsize=(9, 7), dpi=100)
        for i, (k, lbl) in enumerate((("b_ratio", "doublet fit / model"), ("t_stat", "fit t statistic"), ("t63_s", "step t63 (s)"), ("achieved_deg", "step achieved (deg)"))):
            a = fig.add_subplot(2, 2, i + 1)
            for ax_, c in (("A", "#2a6f97"), ("B", "#bc4749")):
                v = [r[k] for r in rows if r["axis"] == ax_ and r[k] is not None and not r["skipped"]]
                if v: a.hist(v, bins=20, alpha=0.6, color=c, label=f"axis {ax_} (n={len(v)})")
            a.set_xlabel(lbl); a.grid(alpha=0.3); a.legend(fontsize=7)
        fig.suptitle(f"Manoeuvre spread: {summ['n']} flights, {summ['skipped']} skipped, {summ['aborted']} aborted, {summ.get('step_skipped', 0)} steps skipped")
        fig.tight_layout(); embed(self.man_holder, fig)
        self.man_txt.delete("1.0", "end"); self.man_txt.insert("end", json.dumps(summ, indent=1, default=lambda x: round(float(x), 3)))

    # =================================================================== 7 authority / SQ1
    def _tab_authority(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Fin Authority / SQ1")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        self.au_imgs = sorted(glob.glob(os.path.join(SIM, "plots_authority", "*.png")) + glob.glob(os.path.join(SIM, "plots_stabilizer", "*.png"))
                              + glob.glob(os.path.join(SIM, "plots_flight", "*.png")))
        self.au_sel = tk.StringVar()
        cb = ttk.Combobox(bar, textvariable=self.au_sel, values=[os.path.relpath(p, SIM) for p in self.au_imgs], state="readonly", width=60)
        cb.pack(side="left"); cb.bind("<<ComboboxSelected>>", lambda e: self._au_show())
        ttk.Button(bar, text="Re-run authority + stabilizer engines", command=lambda: self._run_engine(["wf_fin_authority.py"], then=["wf_stabilizer.py"])).pack(side="left", padx=8)
        self.au_holder = ttk.Frame(f); self.au_holder.pack(fill="both", expand=True, padx=8)
        self.au_txt = tk.Text(f, height=8, wrap="word"); self.au_txt.pack(fill="x", padx=8, pady=4)
        try:
            pt = json.load(open(os.path.join(SIM, "plots_stabilizer", "planform_trade.json")))
            self.au_txt.insert("end", "Planform / offset trade (wf_stabilizer_planform_trade):\n" + json.dumps(pt, default=float)[:1500])
        except Exception: pass
        if self.au_imgs: cb.current(0); self.after(500, self._au_show)

    def _au_show(self):
        p = os.path.join(SIM, self.au_sel.get())
        if not os.path.exists(p): return
        import matplotlib.image as mpimg
        fig = Figure(figsize=(10, 6.5), dpi=100); a = fig.add_subplot(111); a.imshow(mpimg.imread(p)); a.axis("off")
        fig.tight_layout(); embed(self.au_holder, fig)

    # =================================================================== 8 tunnel bench
    def _tab_tunnel(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Wind Tunnel Bench")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Phase A: one fin on the reflection plate", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, justify="left", text="Servo cradle on two 100 g TAL221 cells, 60 mm apart\nalong the chord, NAU7802 at 80 SPS. t2 sweep: -15..+15 deg,\n0.5 deg steps, 3 s dwell, last 2 s averaged.").pack(anchor="w")
        self.tb = {}
        r = ttk.Frame(left); r.pack(fill="x", pady=2); ttk.Label(r, text="profile", width=14).pack(side="left")
        self.tb["profile"] = tk.StringVar(value="NACA0006")
        ttk.Combobox(r, textvariable=self.tb["profile"], values=list(bench.LE_SUCTION), state="readonly", width=14).pack(side="left")
        for k, lbl, v in (("H", "fin height [mm]", "40"), ("V", "tunnel speed [m/s]", "12"), ("seed", "seed", "0")):
            r = ttk.Frame(left); r.pack(fill="x", pady=2); ttk.Label(r, text=lbl, width=14).pack(side="left")
            self.tb[k] = tk.StringVar(value=v); ttk.Entry(r, textvariable=self.tb[k], width=8).pack(side="left")
        self.tb_cal = tk.BooleanVar(value=True); ttk.Checkbutton(left, text="apply the 2x2 calibration", variable=self.tb_cal).pack(anchor="w")
        self.tb_cmp = tk.BooleanVar(value=True); ttk.Checkbutton(left, text="overlay all four profiles", variable=self.tb_cmp).pack(anchor="w")
        ttk.Button(left, text="Sweep ▶", command=self._tb_run).pack(anchor="w", pady=6)
        self.tb_txt = tk.Text(left, width=46, height=14, wrap="word"); self.tb_txt.pack(fill="x")
        self.tb_holder = ttk.Frame(f); self.tb_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)

    def _tb_run(self):
        p = self.tb["profile"].get(); H = float(self.tb["H"].get()); V = float(self.tb["V"].get()); s = int(self.tb["seed"].get())
        cmp_ = list(bench.LE_SUCTION) if self.tb_cmp.get() else None; cal = self.tb_cal.get()
        self.bg(lambda: bench.tunnel_figure(p, H, V, s, cal, cmp_), "tb")

    def _on_tb(self, val):
        fig, summary = val; embed(self.tb_holder, fig)
        self.tb_txt.delete("1.0", "end"); self.tb_txt.insert("end", "\n".join(summary) + "\n\nThe profile-to-profile differences at 10 deg are "
                                                             "several mN against a standard error near 0.05 mN per point, so the bench "
                                                             "resolves RQ1/RQ2 if the cell noise and flow unsteadiness are near these assumed "
                                                             "values. Measure both on the first run (fan on, no fin) and update bench.py.")

    # =================================================================== 9 motor tester
    def _tab_motor(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Static Motor Tester")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        self.mt = tk.StringVar(value=[n for n in bench.MOTOR_NAMES if "F67W" in n][0] if bench.MOTOR_NAMES else "")
        ttk.Combobox(bar, textvariable=self.mt, values=bench.MOTOR_NAMES, state="readonly", width=18).pack(side="left")
        self.mt_cell = tk.StringVar(value="10"); ttk.Label(bar, text="cell [kg]").pack(side="left", padx=(8, 2))
        ttk.Entry(bar, textvariable=self.mt_cell, width=5).pack(side="left")
        self.mt_sps = tk.StringVar(value="80"); ttk.Label(bar, text="SPS").pack(side="left", padx=(8, 2))
        ttk.Combobox(bar, textvariable=self.mt_sps, values=["10", "80"], width=4).pack(side="left")
        self.mt_seed = tk.StringVar(value="0"); ttk.Label(bar, text="seed").pack(side="left", padx=(8, 2))
        ttk.Entry(bar, textvariable=self.mt_seed, width=4).pack(side="left")
        ttk.Button(bar, text="Fire ▶", command=lambda: embed(self.mt_holder, bench.motor_figure(self.mt.get(), float(self.mt_cell.get()), float(self.mt_sps.get()), int(self.mt_seed.get())))).pack(side="left", padx=8)
        self.mt_holder = ttk.Frame(f); self.mt_holder.pack(fill="both", expand=True, padx=8)

    # =================================================================== 10 super combined
    def _tab_combined(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Super Combined")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        self.sc_n = tk.StringVar(value="300"); ttk.Label(bar, text="flights").pack(side="left")
        ttk.Entry(bar, textvariable=self.sc_n, width=7).pack(side="left", padx=4)
        self.sc_preset = tk.StringVar(value="Typical field")
        ttk.Combobox(bar, textvariable=self.sc_preset, values=list(E.PRESETS), state="readonly", width=18).pack(side="left", padx=4)
        self.sc_btn = ttk.Button(bar, text="Run ▶", command=self._sc_run); self.sc_btn.pack(side="left", padx=6)
        ttk.Button(bar, text="Stop", command=self.cancel_evt.set).pack(side="left")
        self.sc_lbl = ttk.Label(bar, text=""); self.sc_lbl.pack(side="left", padx=10)
        self.sc_fig = Figure(figsize=(11, 7), dpi=100)
        self.sc_ax = [self.sc_fig.add_subplot(2, 2, i + 1) for i in range(4)]
        self.sc_holder = ttk.Frame(f); self.sc_holder.pack(fill="both", expand=True, padx=8)
        self.sc_canvas = embed(self.sc_holder, self.sc_fig); self.sc_rows = []

    def _sc_run(self):
        n = int(self.sc_n.get()); env = E.PRESETS[self.sc_preset.get()]; self.cancel_evt.clear(); self.sc_rows = []
        self.sc_btn.config(state="disabled"); out = os.path.join(DEFAULT_OUT, time.strftime("combined_%Y%m%d_%H%M%S.csv"))
        def job():
            w = datagen.Writer(out, E.OUTCOME_COLS)
            for k, (row, _) in enumerate(E.batch(E.conditions(n, int(time.time()) % 10000, env), dt=0.002, cancel=self.cancel_evt)):
                w.rows([row]); self.q.put(("sc_row", row))
            w.close(); return out
        self.bg(job, "sc_done")

    def _on_sc_row(self, row):
        self.sc_rows.append(row)
        if len(self.sc_rows) % 10 and len(self.sc_rows) > 5: return
        R = self.sc_rows; g = lambda k: np.array([r[k] if r[k] is not None else np.nan for r in R], float)
        a = self.sc_ax
        for x in a: x.clear()
        a[0].scatter(g("wind_ms"), g("apogee_m"), s=6, alpha=0.6); a[0].set(xlabel="wind (m/s)", ylabel="apogee (m)")
        a[1].scatter(g("land_x_m"), g("land_y_m"), s=6, c=g("wind_ms"), cmap="viridis"); a[1].plot([0], [0], "k^"); a[1].set_aspect("equal")
        a[1].set(xlabel="x (m)", ylabel="y (m)", title="landing points")
        a[2].hist(g("tilt_rms_deg")[np.isfinite(g("tilt_rms_deg"))], bins=25, color="#2a6f97"); a[2].set(xlabel="tilt rms, rail to burnout + 2 s (deg)")
        b = g("man_b_ratio_A"); a[3].hist(b[np.isfinite(b)], bins=25, color="#bc4749"); a[3].set(xlabel="doublet M_delta fit / model")
        for x in a: x.grid(alpha=0.3)
        self.sc_fig.tight_layout(); self.sc_canvas.draw_idle()
        ap = g("apogee_m"); self.sc_lbl.config(text=f"{len(R)} flights, apogee {np.nanmean(ap):.0f} +/- {np.nanstd(ap):.0f} m, "
                                                   f"landing r95 {np.nanpercentile(g('land_r_m'), 95):.0f} m")

    def _on_sc_done(self, path):
        self.sc_btn.config(state="normal"); self.last_output = path; self.sc_lbl.config(text=self.sc_lbl.cget("text") + f"  saved {os.path.basename(path)}")

    # =================================================================== 11 engines
    def _tab_engines(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Project Engines")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Single-run engines (Simulations/)", font=("", 12, "bold")).pack(anchor="w", pady=4)
        for lbl, args in ENGINES:
            ttk.Button(left, text=lbl, width=42, command=lambda a=args: self._run_engine(a)).pack(anchor="w", pady=2)
        ttk.Button(left, text="Open Simulations folder", command=lambda: self._open(SIM)).pack(anchor="w", pady=10)
        self.en_txt = tk.Text(f, wrap="none", bg="#111", fg="#ddd", font=("Menlo", 10)); self.en_txt.pack(side="left", fill="both", expand=True, padx=8, pady=6)

    def _run_engine(self, args, then=None):
        self.en_txt.insert("end", f"\n$ python3 {' '.join(args)}\n")
        def job():
            p = subprocess.Popen([sys.executable, "-u"] + args, cwd=SIM, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for ln in p.stdout: self.q.put(("en_line", ln))
            p.wait()
            if then: self.q.put(("en_then", then))
            return f"exit {p.returncode}"
        self.bg(job, "en_done")
    def _on_en_line(self, ln):
        if hasattr(self, "en_txt"): self.en_txt.insert("end", ln); self.en_txt.see("end")
    def _on_en_then(self, args): self._run_engine(args)
    def _on_en_done(self, s): self._on_en_line(s + "\n")

    # =================================================================== 12 about
    def _tab_about(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="About")
        t = tk.Text(f, wrap="word", font=("", 11)); t.pack(fill="both", expand=True, padx=12, pady=10)
        try: cn = json.load(open(os.path.join(SIM, "canonical_numbers.json")))
        except Exception: cn = {}
        m = cn.get("motors", cn).get(C.FLIGHT_MOTOR, {}) if isinstance(cn, dict) else {}
        t.insert("end", "GTR70E WYVERN, fin-controlled research rocket: simulation & dataset suite\n\n"
                 f"Airframe: {C.OD:.0f} mm OD, {C.L_TOTAL:.0f} mm long, four KST X08 Plus servo-driven control fins at one station, "
                 f"four {C.RECT_FIN['span']:.0f} mm stabilizers at {C.RECT_FIN['az0_deg']:.0f} deg.\n"
                 f"Motor: {C.FLIGHT_MOTOR}. Liftoff {m.get('liftoff_g', '?')} g, margin {m.get('margin_liftoff_cal', '?')} cal at liftoff, "
                 f"{m.get('margin_burnout_cal', '?')} at burnout.\n"
                 f"Gains: {F.GAINS_FLIGHT}\n\n"
                 "Physics: wf_core.py (geometry, masses, Barrowman + slender-body interference, boundary layer, vortex "
                 "interference, drag build-up, motor .eng curves) and wf_flightsim.py (3-DOF pitch plane, q-scheduled PID, "
                 "rate-limited servo with hinge-load droop, Dryden-like turbulence). The suite only samples conditions and "
                 "calls those.\n\nModel limits: pitch plane only (no roll, no cross-axis coupling); potential-flow fin "
                 "aerodynamics (no stall); single rolled-up vortex interference (pessimistic). The SimScale package in "
                 "CFD/simscale is there to check the last two.\n\nKeys: F11 fullscreen, Esc to leave it.")
        t.config(state="disabled")


def main():
    Suite().mainloop()

if __name__ == "__main__":
    main()
