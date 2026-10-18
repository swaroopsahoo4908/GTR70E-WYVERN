#!/usr/bin/env python3
"""
GTR70E WYVERN, Simulation & Dataset Suite (single desktop GUI).

Tabs:
  1. Atmospheric Datasets : Monte-Carlo generator (outcomes / time-series / TVC) with envelope
     presets, seed, preview count + real ETA, progress bar, live log, working Cancel, open-folder.
  2. Plots & Analysis : load any generated dataset and build histograms / scatter / density
     (hexbin) / altitude-trajectory overlays / correlation heatmaps in an embedded matplotlib
     canvas with the standard zoom/pan/save toolbar, plus a per-column statistics panel.
  3. Data Viewer : tabular Parquet/CSV viewer -- full column headers, numeric formatting +
     right-align, horizontal/vertical scroll, click-to-sort, windowed reads (fast on huge files).
  4. PID Tuner : live closed-loop TVC tuning -- drag Kp/Ki/Kd (+ gimbal limit, wind,
     disturbance) and watch pitch/gimbal response redraw in real time vs the firmware defaults;
     Auto-tune runs a robust multi-wind gain search.
  5. Flight Computer SIL : software-in-the-loop digital twin -- state machine + 500 Hz PID on noisy
     sensors + motor-ejection recovery, streaming simulated Wi-Fi telemetry to a live console.
  6. Super Combined : live-simulates the full closed-loop SIL over N random-condition flights
     (default 25,000), accumulating a live scatter and saving log + per-flight-summary datasets.
  7. Static Motor Tester : pick a motor -> thrust curve + static-stand axial load-cell trace.
  8. Jetvane Suitability : RETIRED 2026-08 (jetvane dropped from the program). Informational only
                            -- it is the analysis that justified dropping it: any printed vane
                            ablates in a 1150 K BP exhaust.
  9. Ground TVC + PID : 3-axis TVC balance reading while the firmware PID gimbals the nozzle.
  10. Project Engines : one-click launchers for the project's single-run sim engines (we4_*.py).
  11. About : canonical vehicle specs + notes.

Opens maximized (fill screen); F11 toggles true fullscreen, Esc exits it.
Requires: numpy, matplotlib, tkinter (+ pyarrow for Parquet). Launch: python3 run_gui.py
"""
import os, sys, time, threading, queue, subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

try:
    from . import core, datagen, analysis, fc_sil, pid_autotune, bench_sim
except ImportError:
    import core, datagen, analysis, fc_sil, pid_autotune, bench_sim

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(HERE, "datasets")

ENGINES = [
    ("Flight trajectory (RK4+Barrowman)", "we4_flightsim.py"),
    ("Ejection / recovery feasibility", "we4_ejection_feasibility.py"),
    ("Stability & fin sizing", "we4_stability.py"),
    ("Atmospheric TVC sweep", "we4_atmos_tvc.py"),
    ("Validation (Monte-Carlo gates)", "we4_validation.py"),
    ("Deep sim (2nd-tier checks)", "we4_deepsim.py"),
    ("Motor trade study", "we4_motor_tradestudy.py"),
]

ENVELOPE_FIELDS = [
    ("wind_ms", "Wind speed [m/s]", 0.0, 15.0),
    ("turb_pct", "Turbulence [%]", 0.0, 30.0),
    ("temp_C", "Surface temp [C]", -15.0, 40.0),
    ("pressure_mbar", "Pressure [mbar]", 985.0, 1030.0),
    ("launch_tilt_deg", "Launch tilt [deg]", 0.0, 8.0),
    ("site_alt_m", "Site elevation [m]", 0.0, 300.0),
    ("wind_dir_deg", "Wind bearing [deg]", 0.0, 360.0),
]

# dark grid palette for the Data Viewer
GRID_BG = "#141414" # cell background (dark)
GRID_HEAD_BG = "#000000" # header background (darker)
GRID_LINE = "#ffffff" # white outlines
GRID_FG = "#ffffff" # white text


class GridTable(ttk.Frame):
    """Virtualized dark table with real white gridlines (thin columns, thicker rows).

    ttk.Treeview cannot draw internal cell borders, so the body is drawn on a tk.Canvas.
    Only the on-screen rows are rendered, so 10k+ row windows stay responsive. Click a
    header cell to sort (delegated to on_sort)."""
    ROWH = 30 # row height (thicker rows)
    PAD = 12 # cell text left padding
    ROW_LINE = 2 # horizontal (row) line width -- a little thicker
    COL_LINE = 1 # vertical (column) line width

    def __init__(self, master, on_sort=None):
        super().__init__(master)
        self.on_sort = on_sort
        self.cols, self.rows, self.numeric = [], [], set()
        self.colw, self.colx, self.total_w = [], [], 0
        self.sort_col, self.sort_rev = None, False
        self._top = 0 # first visible row index
        self._xoff = 0 # horizontal pixel offset

        try:
            self._font = tkfont.nametofont("TkDefaultFont").copy()
        except Exception:
            self._font = tkfont.Font(family="TkDefaultFont", size=10)
        self._measure = self._font.measure

        self.header = tk.Canvas(self, height=self.ROWH, bg=GRID_HEAD_BG,
                                highlightthickness=0, bd=0)
        self.body = tk.Canvas(self, bg=GRID_BG, highlightthickness=0, bd=0)
        self.vs = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.hs = ttk.Scrollbar(self, orient="horizontal", command=self._xview)
        self.header.grid(row=0, column=0, sticky="ew")
        self.body.grid(row=1, column=0, sticky="nsew")
        self.vs.grid(row=1, column=1, sticky="ns")
        self.hs.grid(row=2, column=0, sticky="ew")
        self.rowconfigure(1, weight=1); self.columnconfigure(0, weight=1)

        self.body.bind("<Configure>", lambda e: self._redraw())
        self.body.bind("<MouseWheel>", self._on_wheel) # macOS / Windows
        self.body.bind("<Button-4>", lambda e: self._wheel(-3)) # X11 up
        self.body.bind("<Button-5>", lambda e: self._wheel(+3)) # X11 down
        self.header.bind("<Button-1>", self._on_header_click)

    # ---- data -------------------------------------------------------------
    def set_data(self, cols, rows, numeric, sort_col=None, sort_rev=False):
        self.cols, self.rows, self.numeric = list(cols), list(rows), set(numeric or ())
        self.sort_col, self.sort_rev = sort_col, sort_rev
        self._top = 0
        self._layout_columns()
        self._redraw()

    def _layout_columns(self):
        self.colw = []
        sample = self.rows[:60]
        for j, c in enumerate(self.cols):
            w = self._measure(str(c)) + 24 # header + arrow room
            for r in sample:
                if j < len(r):
                    w = max(w, self._measure(str(r[j])))
            self.colw.append(min(w + 2 * self.PAD, 360))
        self.colx = [0]
        for w in self.colw:
            self.colx.append(self.colx[-1] + w)
        self.total_w = self.colx[-1] if self.colx else 0

    # ---- scrolling --------------------------------------------------------
    def _nvis(self):
        h = max(1, self.body.winfo_height())
        return max(1, h // self.ROWH + 2)

    def _max_top(self):
        return max(0, len(self.rows) - (self._nvis() - 1))

    def _yview(self, *args):
        n = len(self.rows)
        if not n:
            return
        if args[0] == "moveto":
            self._top = int(float(args[1]) * n)
        elif args[0] == "scroll":
            step = int(args[1]) * (self._nvis() - 2 if args[2] == "pages" else 1)
            self._top += step
        self._top = max(0, min(self._top, self._max_top()))
        self._redraw()

    def _xview(self, *args):
        view = max(1, self.body.winfo_width())
        span = max(0, self.total_w - view)
        if args[0] == "moveto":
            self._xoff = int(float(args[1]) * span)
        elif args[0] == "scroll":
            self._xoff += int(args[1]) * 40
        self._xoff = max(0, min(self._xoff, span))
        self._redraw()

    def _on_wheel(self, e):
        self._wheel(-1 if e.delta > 0 else 1)

    def _wheel(self, step):
        self._top = max(0, min(self._top + step, self._max_top()))
        self._redraw()

    def _on_header_click(self, e):
        x = e.x + self._xoff
        for j in range(len(self.cols)):
            if self.colx[j] <= x < self.colx[j + 1]:
                if self.on_sort:
                    self.on_sort(self.cols[j])
                break

    # ---- drawing ----------------------------------------------------------
    def _redraw(self):
        self.header.delete("all"); self.body.delete("all")
        if not self.cols:
            return
        view_w = max(1, self.body.winfo_width())
        n = len(self.rows)
        # scrollbar thumbs
        if n:
            nv = self._nvis() - 1
            self.vs.set(self._top / n, min(1.0, (self._top + nv) / n))
        else:
            self.vs.set(0, 1)
        if self.total_w:
            self.hs.set(self._xoff / self.total_w, min(1.0, (self._xoff + view_w) / self.total_w))

        # ---- header row
        for j, c in enumerate(self.cols):
            x0 = self.colx[j] - self._xoff
            if x0 > view_w or self.colx[j + 1] - self._xoff < 0:
                continue
            self.header.create_line(x0, 0, x0, self.ROWH, fill=GRID_LINE, width=self.COL_LINE)
            arrow = ""
            if c == self.sort_col:
                arrow = " ▲" if not self.sort_rev else " ▼"
            self.header.create_text(x0 + self.PAD, self.ROWH // 2, anchor="w",
                                    text=str(c) + arrow, fill=GRID_FG, font=self._font)
        # header right edge + baseline (thicker, like a row line)
        self.header.create_line(self.total_w - self._xoff, 0, self.total_w - self._xoff,
                                self.ROWH, fill=GRID_LINE, width=self.COL_LINE)
        self.header.create_line(0, self.ROWH - 1, view_w, self.ROWH - 1, fill=GRID_LINE,
                                width=self.ROW_LINE)

        # ---- body rows (virtualized)
        nv = self._nvis()
        end = min(n, self._top + nv)
        right = min(view_w, self.total_w - self._xoff)
        for vi, ri in enumerate(range(self._top, end)):
            y0 = vi * self.ROWH
            self.body.create_line(0, y0, right, y0, fill=GRID_LINE, width=self.ROW_LINE)
            r = self.rows[ri]
            for j, c in enumerate(self.cols):
                x0 = self.colx[j] - self._xoff
                if x0 > view_w or self.colx[j + 1] - self._xoff < 0:
                    continue
                val = str(r[j]) if j < len(r) else ""
                if c in self.numeric:
                    self.body.create_text(self.colx[j + 1] - self._xoff - self.PAD,
                                          y0 + self.ROWH // 2, anchor="e", text=val,
                                          fill=GRID_FG, font=self._font)
                else:
                    self.body.create_text(x0 + self.PAD, y0 + self.ROWH // 2, anchor="w",
                                          text=val, fill=GRID_FG, font=self._font)
        # vertical column lines over the drawn rows
        drawn_h = (end - self._top) * self.ROWH
        for j in range(len(self.cols) + 1):
            x0 = self.colx[j] - self._xoff
            if -1 <= x0 <= view_w + 1:
                self.body.create_line(x0, 0, x0, drawn_h, fill=GRID_LINE, width=self.COL_LINE)
        # bottom edge
        self.body.create_line(0, drawn_h, right, drawn_h, fill=GRID_LINE, width=self.ROW_LINE)


PRESETS = {
    "Typical field": dict(wind_ms=(0, 8), turb_pct=(0, 15), temp_C=(5, 30), pressure_mbar=(995, 1025),
                          launch_tilt_deg=(0, 5), site_alt_m=(0, 200), wind_dir_deg=(0, 360)),
    "Calm": dict(wind_ms=(0, 2), turb_pct=(0, 5), temp_C=(10, 25), pressure_mbar=(1005, 1020),
                          launch_tilt_deg=(0, 2), site_alt_m=(0, 100), wind_dir_deg=(0, 360)),
    "High wind": dict(wind_ms=(8, 15), turb_pct=(15, 30), temp_C=(5, 30), pressure_mbar=(990, 1025),
                          launch_tilt_deg=(2, 8), site_alt_m=(0, 200), wind_dir_deg=(0, 360)),
    "Hot & high": dict(wind_ms=(0, 8), turb_pct=(0, 15), temp_C=(30, 40), pressure_mbar=(985, 1000),
                          launch_tilt_deg=(0, 5), site_alt_m=(200, 300), wind_dir_deg=(0, 360)),
    "Full envelope": dict(wind_ms=(0, 15), turb_pct=(0, 30), temp_C=(-15, 40), pressure_mbar=(985, 1030),
                          launch_tilt_deg=(0, 8), site_alt_m=(0, 300), wind_dir_deg=(0, 360)),
}


class Suite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GTR70E WYVERN, Simulation & Dataset Suite")
        try: # old macOS system Tk 8.5 fails to paint 'aqua'
            style = ttk.Style(self)
            mm = tuple(int(x) for x in self.tk.call("info", "patchlevel").split(".")[:2])
            if mm < (8, 6) and "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass
        self.q = queue.Queue()
        self.cancel_evt = threading.Event()
        self.worker = None
        self.dataset = None # loaded {col: array}
        self.dataset_cols = []
        self.last_output = None # last generated file path

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.nb = nb
        self._build_dataset_tab(nb)
        self._build_plots_tab(nb)
        self._build_viewer_tab(nb)
        self._build_pid_tab(nb)
        self._build_sil_tab(nb)
        self._build_combined_tab(nb)
        self._build_motor_tab(nb)
        self._build_jetvane_tab(nb)
        self._build_groundtvc_tab(nb)
        self._build_engines_tab(nb)
        self._build_about_tab(nb)

        # fill the screen; F11 toggles true fullscreen
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        try: self.state("zoomed")
        except Exception: pass
        self._fs = False
        self.bind("<F11>", self._toggle_fs)
        self.bind("<Escape>", lambda e: self._set_fs(False))
        self.after(120, self._drain_queue)

    def _toggle_fs(self, _=None): self._set_fs(not self._fs)
    def _set_fs(self, on):
        self._fs = on
        try: self.attributes("-fullscreen", on)
        except Exception: pass

    # =============================================================== dataset tab
    def _build_dataset_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Atmospheric Datasets")
        top = ttk.LabelFrame(f, text="Dataset type"); top.pack(fill="x", padx=8, pady=6)
        self.kind = tk.StringVar(value="outcomes")
        for i, (k, lbl) in enumerate([("outcomes", "Per-flight outcomes"),
                                      ("timeseries", "Full time-series states"),
                                      ("tvc", "TVC control performance")]):
            ttk.Radiobutton(top, text=lbl, variable=self.kind, value=k,
                            command=self._sync_fields).grid(row=0, column=i, padx=10, pady=4, sticky="w")

        row = ttk.Frame(f); row.pack(fill="x", padx=8, pady=2)
        ttk.Label(row, text="Flights (N):").grid(row=0, column=0, sticky="w")
        self.n_var = tk.StringVar(value="1000000")
        ttk.Entry(row, textvariable=self.n_var, width=12).grid(row=0, column=1, padx=4)
        self.stride_lbl = ttk.Label(row, text="Trace stride:")
        self.stride_var = tk.StringVar(value="10")
        self.stride_ent = ttk.Entry(row, textvariable=self.stride_var, width=6)
        ttk.Label(row, text="Seed:").grid(row=0, column=6, padx=(16, 2))
        self.seed_var = tk.StringVar(value="0")
        ttk.Entry(row, textvariable=self.seed_var, width=8).grid(row=0, column=7)
        ttk.Label(row, text="Format:").grid(row=0, column=8, padx=(16, 2))
        self.fmt_var = tk.StringVar(value="auto")
        ttk.Combobox(row, textvariable=self.fmt_var, values=["auto", "parquet", "csv"],
                     width=8, state="readonly").grid(row=0, column=9)
        self.ts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text="New file each run (timestamp)", variable=self.ts_var).grid(
            row=0, column=10, padx=(16, 0))

        pre = ttk.LabelFrame(f, text="Envelope presets"); pre.pack(fill="x", padx=8, pady=4)
        for i, name in enumerate(PRESETS):
            ttk.Button(pre, text=name, command=lambda n=name: self._apply_preset(n)).grid(
                row=0, column=i, padx=4, pady=3)

        env = ttk.LabelFrame(f, text="Sampling envelope (min / max)"); env.pack(fill="x", padx=8, pady=4)
        self.env_vars = {}
        for r, (key, lbl, lo, hi) in enumerate(ENVELOPE_FIELDS):
            ttk.Label(env, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=1)
            vlo = tk.StringVar(value=str(lo)); vhi = tk.StringVar(value=str(hi))
            ttk.Entry(env, textvariable=vlo, width=9).grid(row=r, column=1, padx=2)
            ttk.Entry(env, textvariable=vhi, width=9).grid(row=r, column=2, padx=2)
            self.env_vars[key] = (vlo, vhi)

        outf = ttk.Frame(f); outf.pack(fill="x", padx=8, pady=4)
        ttk.Label(outf, text="Output:").grid(row=0, column=0, sticky="w")
        self.out_var = tk.StringVar(value=os.path.join(DEFAULT_OUT, "wyvern_outcomes.parquet"))
        ttk.Entry(outf, textvariable=self.out_var, width=70).grid(row=0, column=1, padx=4)
        ttk.Button(outf, text="Browse…", command=self._browse_out).grid(row=0, column=2)
        ttk.Button(outf, text="Open folder", command=lambda: self._os_open(DEFAULT_OUT)).grid(row=0, column=3, padx=4)

        btns = ttk.Frame(f); btns.pack(fill="x", padx=8, pady=4)
        ttk.Button(btns, text="Preview count & ETA", command=self._preview).pack(side="left")
        self.go_btn = ttk.Button(btns, text="Generate", command=self._start); self.go_btn.pack(side="left", padx=6)
        self.cancel_btn = ttk.Button(btns, text="Cancel", command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left")
        ttk.Button(btns, text="Quick nominal flight ▶", command=self._nominal_flight).pack(side="right")

        self.pbar = ttk.Progressbar(f, mode="determinate"); self.pbar.pack(fill="x", padx=8, pady=4)
        self.log = tk.Text(f, height=12, wrap="word"); self.log.pack(fill="both", expand=True, padx=8, pady=4)
        self._sync_fields()
        self._logln("Ready. Parquet %s. F11 = fullscreen." %
                    ("available" if datagen.HAVE_PARQUET else "unavailable (CSV fallback)"))

    def _apply_preset(self, name):
        for key, (lo, hi) in PRESETS[name].items():
            vlo, vhi = self.env_vars[key]; vlo.set(str(lo)); vhi.set(str(hi))
        self._logln(f"Applied preset: {name}")

    def _sync_fields(self):
        if self.kind.get() == "timeseries":
            self.stride_lbl.grid(row=0, column=2, padx=(16, 2)); self.stride_ent.grid(row=0, column=3)
        else:
            self.stride_lbl.grid_remove(); self.stride_ent.grid_remove()
        base = {"outcomes": "wyvern_outcomes", "timeseries": "wyvern_timeseries", "tvc": "wyvern_tvc"}[self.kind.get()]
        ext = ".parquet" if datagen.HAVE_PARQUET else ".csv.gz"
        if os.path.dirname(self.out_var.get()) == DEFAULT_OUT or not self.out_var.get():
            self.out_var.set(os.path.join(DEFAULT_OUT, base + ext))

    def _envelope(self):
        env = {}
        for key, (vlo, vhi) in self.env_vars.items():
            try: env[key] = (float(vlo.get()), float(vhi.get()))
            except ValueError: raise ValueError(f"Envelope field '{key}' must be numeric.")
        return env

    def _browse_out(self):
        ext = ".parquet" if datagen.HAVE_PARQUET else ".csv.gz"
        p = filedialog.asksaveasfilename(defaultextension=ext, initialdir=DEFAULT_OUT,
                                         initialfile=os.path.basename(self.out_var.get()))
        if p: self.out_var.set(p)

    def _preview(self):
        try:
            kind = self.kind.get()
            if kind == "timeseries":
                flights = int(self.n_var.get()); rows, note = datagen.estimate(
                    "timeseries", flights=flights, stride=int(self.stride_var.get()))
            else:
                rows, note = datagen.estimate(kind, n=int(self.n_var.get()))
        except ValueError:
            messagebox.showerror("Preview", "N (and stride) must be integers."); return
        self._logln("Timing a 2,000-flight sample to estimate throughput…")
        def _measure():
            t0 = time.time(); s = int(self.stride_var.get() or 10)
            if kind == "outcomes": core.simulate_outcomes(2000, seed=7)
            elif kind == "tvc": core.simulate_tvc(2000, seed=7)
            else: core.simulate_trace(2000, seed=7, trace_stride=s)
            rate = 2000 / max(time.time() - t0, 1e-9)
            eta = int(self.n_var.get()) / max(rate, 1e-9)
            self.q.put(("log", f"{note}\n ~{rate:,.0f} flights/s -> ETA ~{eta/60:.1f} min "
                               f"({eta:.0f} s) for {int(self.n_var.get()):,} flights"))
        threading.Thread(target=_measure, daemon=True).start()

    def _start(self):
        if self.worker and self.worker.is_alive(): return
        try:
            env = self._envelope(); out = self.out_var.get(); fmt = self.fmt_var.get()
            kind = self.kind.get(); seed = int(self.seed_var.get())
        except ValueError as e:
            messagebox.showerror("Generate", str(e)); return
        self.cancel_evt.clear()
        self.go_btn.config(state="disabled"); self.cancel_btn.config(state="normal"); self.pbar["value"] = 0
        self._logln(f"\n=== generating {kind} -> {out} ===")
        progress_cb = lambda d, t, r, rate: self.q.put(("progress", (d, t, r, rate)))
        cancel_cb = lambda: self.cancel_evt.is_set()
        def run():
            try:
                ts = self.ts_var.get()
                if kind == "outcomes":
                    r = datagen.generate_outcomes(int(self.n_var.get()), out, fmt, seed=seed,
                                                  envelope=env, timestamp=ts,
                                                  progress_cb=progress_cb, cancel_cb=cancel_cb)
                elif kind == "tvc":
                    r = datagen.generate_tvc(int(self.n_var.get()), out, fmt, seed=seed,
                                             envelope=env, timestamp=ts,
                                             progress_cb=progress_cb, cancel_cb=cancel_cb)
                else:
                    r = datagen.generate_timeseries(int(self.n_var.get()), out, fmt, seed=seed,
                                                    stride=int(self.stride_var.get()), envelope=env,
                                                    timestamp=ts, progress_cb=progress_cb, cancel_cb=cancel_cb)
                self.q.put(("done", r))
            except Exception as e:
                self.q.put(("error", repr(e)))
        self.worker = threading.Thread(target=run, daemon=True); self.worker.start()

    def _cancel(self):
        self.cancel_evt.set(); self._logln("Cancel requested, finishing current chunk…")

    def _nominal_flight(self):
        """Run one calm nominal flight and show its altitude/velocity trace in the Plots tab."""
        self._logln("Running nominal single flight…")
        def run():
            nominal = dict(wind_ms=(0, 0), turb_pct=(0, 0), temp_C=(15, 15), pressure_mbar=(1013.25, 1013.25),
                           launch_tilt_deg=(0, 0), site_alt_m=(0, 0), wind_dir_deg=(0, 0))
            out, tr, cond = core.simulate_trace(1, seed=1, envelope=nominal, dt=0.002, trace_stride=5)
            data = {"flight_id": tr["t"][:, 0] * 0, "t": tr["t"][:, 0], "z": tr["z"][:, 0],
                    "vz": tr["vz"][:, 0], "mach": tr["mach"][:, 0], "q": tr["q"][:, 0]}
            self.q.put(("nominal", (data, float(out["apogee_m"][0]), float(out["apogee_t"][0]))))
        threading.Thread(target=run, daemon=True).start()

    # =============================================================== plots tab
    def _build_plots_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Plots & Analysis")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Load dataset…", command=self._load_dataset).pack(side="left")
        ttk.Button(bar, text="Load last generated", command=self._load_last).pack(side="left", padx=6)
        self.ds_lbl = ttk.Label(bar, text="(no dataset loaded)"); self.ds_lbl.pack(side="left", padx=10)

        ctl = ttk.Frame(f); ctl.pack(fill="x", padx=8, pady=2)
        ttk.Label(ctl, text="Plot:").grid(row=0, column=0)
        self.pk_var = tk.StringVar(value=analysis.PLOT_KINDS[0])
        ttk.Combobox(ctl, textvariable=self.pk_var, values=analysis.PLOT_KINDS, width=18,
                     state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(ctl, text="X:").grid(row=0, column=2)
        self.xcol = ttk.Combobox(ctl, width=18, state="readonly"); self.xcol.grid(row=0, column=3, padx=4)
        ttk.Label(ctl, text="Y:").grid(row=0, column=4)
        self.ycol = ttk.Combobox(ctl, width=18, state="readonly"); self.ycol.grid(row=0, column=5, padx=4)
        ttk.Label(ctl, text="bins:").grid(row=0, column=6)
        self.bins_var = tk.StringVar(value="60")
        ttk.Entry(ctl, textvariable=self.bins_var, width=5).grid(row=0, column=7, padx=4)
        ttk.Button(ctl, text="Plot", command=self._plot).grid(row=0, column=8, padx=8)
        ttk.Button(ctl, text="Column stats", command=self._stats).grid(row=0, column=9)

        body = ttk.Frame(f); body.pack(fill="both", expand=True, padx=8, pady=4)
        self.plot_holder = ttk.Frame(body); self.plot_holder.pack(side="left", fill="both", expand=True)
        self.stats_txt = tk.Text(body, width=42, wrap="word"); self.stats_txt.pack(side="right", fill="y")
        self.stats_txt.insert("end", "Load a dataset, then Plot or Column stats.\n\n"
                              "Plot kinds:\n • Histogram (pick X)\n • Scatter (X vs Y)\n"
                              " • Density hexbin (X vs Y, great for millions)\n"
                              " • Trajectories (time-series only)\n • Correlation heatmap\n")
        self._canvas = None; self._toolbar = None

    def _load_dataset(self):
        p = filedialog.askopenfilename(initialdir=DEFAULT_OUT,
                                       filetypes=[("datasets", "*.parquet *.csv *.gz"), ("all", "*.*")])
        if p: self._do_load(p)

    def _load_last(self):
        if self.last_output and os.path.exists(self.last_output): self._do_load(self.last_output)
        else: messagebox.showinfo("Load", "No generated dataset yet this session.")

    def _do_load(self, path):
        self.ds_lbl.config(text="loading…")
        def run():
            try:
                data, cols, ntot, nload = analysis.load_dataset(path)
                self.q.put(("dataset", (path, data, cols, ntot, nload)))
            except Exception as e:
                self.q.put(("error", f"load failed: {e!r}"))
        threading.Thread(target=run, daemon=True).start()

    def _plot(self):
        if not self.dataset:
            messagebox.showinfo("Plot", "Load a dataset first."); return
        try: bins = int(self.bins_var.get())
        except ValueError: bins = 60
        fig = analysis.make_figure(self.pk_var.get(), self.dataset,
                                   xcol=self.xcol.get() or None, ycol=self.ycol.get() or None, bins=bins)
        self._embed(fig)

    def _embed(self, fig):
        for w in self.plot_holder.winfo_children(): w.destroy()
        self._canvas = FigureCanvasTkAgg(fig, master=self.plot_holder)
        self._canvas.draw()
        self._toolbar = NavigationToolbar2Tk(self._canvas, self.plot_holder, pack_toolbar=False)
        self._toolbar.update()
        self._toolbar.pack(side="top", fill="x")
        self._canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def _stats(self):
        if not self.dataset:
            messagebox.showinfo("Stats", "Load a dataset first."); return
        c = self.xcol.get()
        if not c: messagebox.showinfo("Stats", "Pick a column in X first."); return
        self.stats_txt.delete("1.0", "end")
        self.stats_txt.insert("end", analysis.column_stats(self.dataset, c))

    # =============================================================== Data Viewer tab
    def _build_viewer_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Data Viewer")
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Load file…", command=self._viewer_browse).pack(side="left")
        ttk.Button(bar, text="Load last generated", command=self._viewer_last).pack(side="left", padx=6)
        ttk.Label(bar, text="Start row:").pack(side="left", padx=(12, 2))
        self.vw_start = tk.StringVar(value="0")
        ttk.Entry(bar, textvariable=self.vw_start, width=9).pack(side="left")
        ttk.Label(bar, text="Rows:").pack(side="left", padx=(8, 2))
        self.vw_limit = tk.StringVar(value="10000")
        ttk.Entry(bar, textvariable=self.vw_limit, width=7).pack(side="left")
        ttk.Button(bar, text="Reload", command=self._viewer_reload).pack(side="left", padx=6)
        self.vw_info = ttk.Label(bar, text="(no file loaded)"); self.vw_info.pack(side="left", padx=12)
        self._vw_holder = ttk.Frame(f); self._vw_holder.pack(fill="both", expand=True, padx=8, pady=4)
        ttk.Label(f, text="Tip: click a column header to sort the loaded rows; scroll horizontally for wide tables.",
                  foreground="#667").pack(anchor="w", padx=10, pady=(0, 4))
        self._vw_path = None; self._vw_cols = []; self._vw_rows = []; self._vw_numeric = set()
        self._vw_total = None; self._vw_sort = (None, False); self._vw_tree = None

    def _viewer_browse(self):
        p = filedialog.askopenfilename(initialdir=DEFAULT_OUT,
                                       filetypes=[("data files", "*.parquet *.csv *.gz"), ("all", "*.*")])
        if p:
            self._vw_path = p; self.vw_start.set("0"); self._viewer_reload()

    def _viewer_last(self):
        if self.last_output and os.path.exists(self.last_output):
            self._vw_path = self.last_output; self.vw_start.set("0"); self._viewer_reload()
        else:
            messagebox.showinfo("Data Viewer", "No generated dataset yet this session.")

    def _viewer_reload(self):
        if not self._vw_path:
            messagebox.showinfo("Data Viewer", "Load a file first."); return
        try:
            start = int(self.vw_start.get()); limit = int(self.vw_limit.get())
        except ValueError:
            messagebox.showerror("Data Viewer", "Start row and Rows must be integers."); return
        self.vw_info.config(text="loading…")
        path = self._vw_path
        def run():
            try:
                r = analysis.load_table(path, start=start, limit=limit)
                r["_start"] = start; r["_path"] = path
                self.q.put(("viewer", r))
            except Exception as e:
                self.q.put(("error", f"viewer load failed: {e!r}"))
        threading.Thread(target=run, daemon=True).start()

    def _viewer_populate(self):
        cols = self._vw_cols
        if not cols:
            return
        if self._vw_tree is None or not self._vw_tree.winfo_exists():
            for w in self._vw_holder.winfo_children():
                w.destroy()
            self._vw_tree = GridTable(self._vw_holder, on_sort=self._viewer_sort)
            self._vw_tree.pack(fill="both", expand=True)
        sort_col, sort_rev = self._vw_sort
        self._vw_tree.set_data(cols, self._vw_rows, self._vw_numeric,
                               sort_col=sort_col, sort_rev=sort_rev)

    def _viewer_sort(self, col):
        if col not in self._vw_cols:
            return
        j = self._vw_cols.index(col)
        prev, rev = self._vw_sort
        rev = (not rev) if prev == col else False
        def key(r):
            v = r[j] if j < len(r) else ""
            try:
                return (0, float(v))
            except (ValueError, TypeError):
                return (1, v)
        self._vw_rows = sorted(self._vw_rows, key=key, reverse=rev)
        self._vw_sort = (col, rev)
        self._viewer_populate()

    # =============================================================== PID tuner tab
    def _build_pid_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="PID Tuner")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Live TVC pitch-loop tuning", font=("", 12, "bold")).pack(anchor="w")

        self.pid_vars = {}
        self.pid_val_lbls = {}
        def slider(parent, key, label, lo, hi, init, res=0.01):
            rowf = ttk.Frame(parent); rowf.pack(fill="x", pady=2)
            ttk.Label(rowf, text=label, width=16).pack(side="left")
            var = tk.DoubleVar(value=init)
            vlbl = ttk.Label(rowf, text=f"{init:.2f}", width=6); vlbl.pack(side="right")
            sc = ttk.Scale(rowf, from_=lo, to=hi, variable=var, orient="horizontal",
                           command=lambda _v, k=key: self._pid_mark_dirty())
            sc.pack(side="left", fill="x", expand=True, padx=6)
            self.pid_vars[key] = var; self.pid_val_lbls[key] = (vlbl, res)
            return var

        gains = ttk.LabelFrame(left, text="Gains"); gains.pack(fill="x", pady=4)
        slider(gains, "kp", "Kp", 0.0, 1.0, core.KP)
        slider(gains, "ki", "Ki", 0.0, 2.0, core.KI)
        slider(gains, "kd", "Kd", 0.0, 1.0, core.KD)

        cond = ttk.LabelFrame(left, text="Conditions"); cond.pack(fill="x", pady=4)
        slider(cond, "gimbal_deg", "Gimbal limit °", 1.0, 10.0, 8.0, res=0.1)
        slider(cond, "wind", "Wind m/s", 0.0, 15.0, 6.0, res=0.1)
        slider(cond, "turb", "Turbulence %", 0.0, 30.0, 10.0, res=0.1)
        drow = ttk.Frame(cond); drow.pack(fill="x", pady=2)
        ttk.Label(drow, text="Disturbance", width=16).pack(side="left")
        self.pid_dist = tk.StringVar(value="Wind gust")
        ttk.Combobox(drow, textvariable=self.pid_dist, state="readonly", width=18,
                     values=["Wind gust", "Initial tip 10 deg"]).pack(side="left")
        self.pid_dist.trace_add("write", lambda *a: self._pid_mark_dirty())

        opts = ttk.Frame(left); opts.pack(fill="x", pady=4)
        self.pid_live = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Live update", variable=self.pid_live).pack(side="left")
        self.pid_overlay = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Show firmware default", variable=self.pid_overlay,
                        command=self._pid_mark_dirty).pack(side="left", padx=8)
        btns = ttk.Frame(left); btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Reset to firmware", command=self._pid_reset).pack(side="left")
        ttk.Button(btns, text="Recompute", command=self._pid_compute).pack(side="left", padx=6)
        btns2 = ttk.Frame(left); btns2.pack(fill="x", pady=2)
        self.pid_autotune_btn = ttk.Button(btns2, text="Auto-tune (robust ~10 s)", command=self._pid_autotune)
        self.pid_autotune_btn.pack(side="left")
        ttk.Button(btns2, text="Apply best", command=self._pid_apply_best).pack(side="left", padx=6)
        self.pid_metrics = tk.Text(left, width=34, height=9, wrap="word")
        self.pid_metrics.pack(fill="x", pady=6)

        self._pid_fig = Figure(figsize=(7.5, 6), dpi=100)
        self._pid_ax_t = self._pid_fig.add_subplot(211)
        self._pid_ax_d = self._pid_fig.add_subplot(212)
        holder = ttk.Frame(f); holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self._pid_canvas = FigureCanvasTkAgg(self._pid_fig, master=holder)
        self._pid_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._pid_dirty = True
        self.after(200, self._pid_tick)

    def _pid_mark_dirty(self):
        self._pid_dirty = True
        # refresh the numeric labels next to each slider
        for k, (lbl, res) in self.pid_val_lbls.items():
            fmt = "%.2f" if res >= 0.01 else "%.1f"
            try: lbl.config(text=fmt % self.pid_vars[k].get())
            except Exception: pass

    def _pid_tick(self):
        if getattr(self, "_pid_dirty", False) and self.pid_live.get():
            self._pid_dirty = False
            self._pid_compute()
        self.after(120, self._pid_tick)

    def _pid_reset(self):
        self.pid_vars["kp"].set(core.KP); self.pid_vars["ki"].set(core.KI); self.pid_vars["kd"].set(core.KD)
        self._pid_mark_dirty(); self._pid_compute()

    def _pid_autotune(self):
        self.pid_autotune_btn.config(state="disabled")
        self.pid_metrics.delete("1.0", "end")
        self.pid_metrics.insert("end", "auto-tuning (robust multi-wind search)… ~10 s")
        def run():
            try:
                best, ranked, fw = pid_autotune.autotune(dt=0.005)
                self.q.put(("autotune", (best, fw)))
            except Exception as e:
                self.q.put(("error", f"autotune failed: {e!r}"))
        threading.Thread(target=run, daemon=True).start()

    def _pid_apply_best(self):
        b = getattr(self, "_autotune_best", None)
        if not b:
            messagebox.showinfo("Auto-tune", "Run Auto-tune first."); return
        self.pid_vars["kp"].set(round(b[1], 3)); self.pid_vars["ki"].set(round(b[2], 3))
        self.pid_vars["kd"].set(round(b[3], 3)); self._pid_mark_dirty(); self._pid_compute()

    def _pid_compute(self):
        g = {k: self.pid_vars[k].get() for k in ("kp", "ki", "kd", "gimbal_deg", "wind", "turb")}
        dist = self.pid_dist.get()
        cur = core.simulate_tvc_trace(kp=g["kp"], ki=g["ki"], kd=g["kd"], gimbal_deg=g["gimbal_deg"],
                                      wind=g["wind"], turb=g["turb"], disturbance=dist)
        for k, (lbl, res) in self.pid_val_lbls.items():
            fmt = "%.2f" if res >= 0.01 else "%.1f"
            try: lbl.config(text=fmt % self.pid_vars[k].get())
            except Exception: pass
        axt, axd = self._pid_ax_t, self._pid_ax_d
        axt.clear(); axd.clear()
        axt.plot(cur["t"], cur["theta_deg"], color="#2a6f97", lw=1.6, label="pitch θ (your gains)")
        axd.plot(cur["t"], cur["delta_deg"], color="#2a6f97", lw=1.2, label="gimbal δ")
        if self.pid_overlay.get():
            dfl = core.simulate_tvc_trace(gimbal_deg=g["gimbal_deg"], wind=g["wind"], turb=g["turb"],
                                          disturbance=dist) # firmware defaults
            axt.plot(dfl["t"], dfl["theta_deg"], color="#999", lw=1.0, ls="--", label="firmware default")
            axd.plot(dfl["t"], dfl["delta_deg"], color="#999", lw=0.9, ls="--")
        axt.axhline(0, color="k", lw=0.5); axt.axvline(core.TVC_ENGAGE_T, color="g", ls=":", lw=0.8)
        axt.set_ylabel("pitch dev θ (deg)"); axt.grid(alpha=0.3); axt.legend(fontsize=8, loc="upper right")
        axt.set_title(f"Closed-loop pitch response, Kp={g['kp']:.2f} Ki={g['ki']:.2f} Kd={g['kd']:.2f}")
        axd.axhline(g["gimbal_deg"], color="#bc4749", ls=":", lw=0.8)
        axd.axhline(-g["gimbal_deg"], color="#bc4749", ls=":", lw=0.8, label="gimbal limit")
        axd.set_xlabel("t (s)"); axd.set_ylabel("gimbal δ (deg)"); axd.grid(alpha=0.3)
        axd.legend(fontsize=8, loc="upper right")
        self._pid_fig.tight_layout(); self._pid_canvas.draw()
        m = cur["metrics"]
        self.pid_metrics.delete("1.0", "end")
        self.pid_metrics.insert("end",
            f"Disturbance: {dist}\n"
            f"peak |θ| {m['peak_pitch_deg']:.2f} deg\n"
            f"steady-state err {m['steady_err_deg']:.2f} deg\n"
            f"settle (<1°) {m['settle_time_s']:.2f} s\n"
            f"RMS gimbal {m['rms_gimbal_deg']:.2f} deg\n"
            f"gimbal saturation {m['gimbal_saturation_pct']:.0f} %\n\n"
            f"firmware default: Kp={core.KP} Ki={core.KI} Kd={core.KD}")

    # =============================================================== Flight-Computer SIL tab
    def _build_sil_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Flight Computer SIL")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Software-in-the-loop flight", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="Runs the FC processes (state machine,\n500 Hz PID on noisy sensors, recovery)\nagainst a simulated flight + atmosphere.",
                  justify="left").pack(anchor="w", pady=2)
        self.sil_vars = {}
        def s(parent, key, label, lo, hi, init, res=0.1):
            r = ttk.Frame(parent); r.pack(fill="x", pady=2)
            ttk.Label(r, text=label, width=15).pack(side="left")
            v = tk.DoubleVar(value=init); lbl = ttk.Label(r, text=f"{init:g}", width=6); lbl.pack(side="right")
            sc = ttk.Scale(r, from_=lo, to=hi, variable=v, orient="horizontal",
                           command=lambda _x, l=lbl, vv=v, rr=res: l.config(text=("%.1f" % vv.get()) if rr < 1 else ("%d" % vv.get())))
            sc.pack(side="left", fill="x", expand=True, padx=6); self.sil_vars[key] = v
        c = ttk.LabelFrame(left, text="Conditions"); c.pack(fill="x", pady=4)
        s(c, "wind", "Wind m/s", 0, 15, 6.0)
        s(c, "turb", "Turbulence %", 0, 30, 12.0)
        s(c, "temp", "Temp °C", -15, 40, 15.0)
        s(c, "seed", "Seed", 0, 50, 1, res=1)
        self.sil_usefw = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Use firmware gains (0.10/0.40/0.18)", variable=self.sil_usefw).pack(anchor="w", pady=2)
        self.sil_btn = ttk.Button(left, text="Run SIL flight ▶", command=self._sil_run); self.sil_btn.pack(fill="x", pady=4)
        self.sil_summary = tk.Text(left, width=36, height=10, wrap="word"); self.sil_summary.pack(fill="x", pady=4)
        ttk.Label(left, text="Simulated Wi-Fi telemetry:").pack(anchor="w")
        self.sil_telem = tk.Text(left, width=36, height=12, wrap="none", bg="#0b1020", fg="#7CFC98",
                                 insertbackground="#7CFC98"); self.sil_telem.pack(fill="both", expand=True)

        holder = ttk.Frame(f); holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self._sil_fig = Figure(figsize=(7.5, 6.2), dpi=100)
        self._sil_axz = self._sil_fig.add_subplot(311)
        self._sil_axp = self._sil_fig.add_subplot(312)
        self._sil_axg = self._sil_fig.add_subplot(313)
        self._sil_canvas = FigureCanvasTkAgg(self._sil_fig, master=holder)
        self._sil_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._sil_tel_buf = []; self._sil_tel_i = 0

    def _sil_run(self):
        self.sil_btn.config(state="disabled")
        self.sil_telem.delete("1.0", "end"); self.sil_summary.delete("1.0", "end")
        self.sil_summary.insert("end", "running SIL…")
        usefw = self.sil_usefw.get()
        gains = (None, None, None) if usefw else (core.KP, core.KI, core.KD)
        wind = self.sil_vars["wind"].get(); turb = self.sil_vars["turb"].get()
        temp = self.sil_vars["temp"].get(); seed = int(self.sil_vars["seed"].get())
        def run():
            try:
                r = fc_sil.run_sil(kp=gains[0], ki=gains[1], kd=gains[2], wind_ms=wind, turb_pct=turb,
                                   temp_C=temp, seed=seed, dt=0.002, hb_hz=8)
                self.q.put(("sil", r))
            except Exception as e:
                self.q.put(("error", f"SIL failed: {e!r}"))
        threading.Thread(target=run, daemon=True).start()

    def _sil_plot(self, r):
        a = r["arr"]; import numpy as np
        axz, axp, axg = self._sil_axz, self._sil_axp, self._sil_axg
        for ax in (axz, axp, axg): ax.clear()
        axz.plot(a["t"], a["z"], "#2a6f97", lw=1.4, label="true alt")
        axz.plot(a["t"], a["baro_alt"], "#f4a261", lw=0.7, alpha=0.7, label="baro (noisy)")
        axz.axvline(core.DEPLOY_T, color="r", ls="--", lw=0.8, label="eject 7.45 s")
        axz.set_ylabel("altitude (m)"); axz.legend(fontsize=7, loc="upper right"); axz.grid(alpha=0.3)
        axz.set_title(f"SIL flight, apogee {r['summary']['apogee_true_m']} m, "
                      f"boost pitch {r['summary']['peak_pitch_boost_deg']}°, land {r['summary']['touchdown_v_ms']} m/s")
        axp.plot(a["t"], a["theta_deg"], "#bc4749", lw=1.0); axp.axhline(0, color="k", lw=0.4)
        axp.set_ylabel("pitch θ (deg)"); axp.grid(alpha=0.3)
        axg.plot(a["t"], a["gimbal_deg"], "#2a9d8f", lw=0.9)
        axg.axhline(5, color="#bc4749", ls=":", lw=0.7); axg.axhline(-5, color="#bc4749", ls=":", lw=0.7)
        axg.set_ylabel("gimbal δ (deg)"); axg.set_xlabel("t (s)"); axg.grid(alpha=0.3)
        self._sil_fig.tight_layout(); self._sil_canvas.draw()

    def _sil_stream(self):
        if self._sil_tel_i < len(self._sil_tel_buf):
            for line in self._sil_tel_buf[self._sil_tel_i:self._sil_tel_i + 3]:
                self.sil_telem.insert("end", line + "\n")
            self.sil_telem.see("end"); self._sil_tel_i += 3
            self.after(80, self._sil_stream)

    # =============================================================== Super Combined tab
    def _build_combined_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Super Combined")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Super Combined SIL batch", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="Live-simulates the full closed-loop TVC\nflight computer over N random-condition\nflights and saves the data (log + summary).",
                  justify="left").pack(anchor="w", pady=2)
        r1 = ttk.Frame(left); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Flights:").pack(side="left")
        self.comb_n = tk.StringVar(value="25000")
        ttk.Entry(r1, textvariable=self.comb_n, width=10).pack(side="left", padx=4)
        ttk.Label(r1, text="Seed:").pack(side="left", padx=(8, 2))
        self.comb_seed = tk.StringVar(value="0")
        ttk.Entry(r1, textvariable=self.comb_seed, width=6).pack(side="left")
        r2 = ttk.Frame(left); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="Envelope:").pack(side="left")
        self.comb_preset = tk.StringVar(value="Full envelope")
        ttk.Combobox(r2, textvariable=self.comb_preset, values=list(PRESETS), width=16,
                     state="readonly").pack(side="left", padx=4)
        r3 = ttk.Frame(left); r3.pack(fill="x", pady=3)
        ttk.Label(r3, text="Output:").pack(side="left")
        self.comb_out = tk.StringVar(value=os.path.join(DEFAULT_OUT, "wyvern_combined.parquet"))
        ttk.Entry(r3, textvariable=self.comb_out, width=26).pack(side="left", padx=4)
        b = ttk.Frame(left); b.pack(fill="x", pady=4)
        self.comb_btn = ttk.Button(b, text="Run batch ▶", command=self._comb_run); self.comb_btn.pack(side="left")
        self.comb_cancel = ttk.Button(b, text="Cancel", command=lambda: self.cancel_evt.set(), state="disabled")
        self.comb_cancel.pack(side="left", padx=6)
        self.comb_pbar = ttk.Progressbar(left, mode="determinate"); self.comb_pbar.pack(fill="x", pady=4)
        self.comb_status = tk.Text(left, width=38, height=13, wrap="word"); self.comb_status.pack(fill="both", expand=True)
        self.comb_status.insert("end", "Set N (default 25,000) and Run. Live scatter builds as flights\ncomplete. A high-fidelity closed-loop batch runs ~14 flights/s\n(25,000 ≈ 30 min); Cancel keeps whatever was written.")

        holder = ttk.Frame(f); holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self._comb_fig = Figure(figsize=(7.5, 6.2), dpi=100)
        self._comb_canvas = FigureCanvasTkAgg(self._comb_fig, master=holder)
        self._comb_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._comb_acc = {"wind": [], "pitch": [], "apogee": [], "sat": []}

    def _comb_run(self):
        if self.worker and self.worker.is_alive(): return
        try:
            n = int(self.comb_n.get()); seed = int(self.comb_seed.get())
        except ValueError:
            messagebox.showerror("Combined", "Flights and Seed must be integers."); return
        env = PRESETS[self.comb_preset.get()]; out = self.comb_out.get()
        self.cancel_evt.clear()
        self.comb_btn.config(state="disabled"); self.comb_cancel.config(state="normal")
        self.comb_pbar["value"] = 0
        self._comb_acc = {"wind": [], "pitch": [], "apogee": [], "sat": []}
        self.comb_status.delete("1.0", "end"); self.comb_status.insert("end", f"running {n:,} SIL flights…\n")
        prog = lambda d, t, rows, rate: self.q.put(("comb_prog", (d, t, rows, rate)))
        samp = lambda recent: self.q.put(("comb_sample", recent))
        canc = lambda: self.cancel_evt.is_set()
        def run():
            try:
                r = datagen.generate_combined(n, out, seed=seed, envelope=env,
                                              progress_cb=prog, sample_cb=samp, cancel_cb=canc)
                self.q.put(("comb_done", r))
            except Exception as e:
                self.q.put(("error", f"combined failed: {e!r}"))
        self.worker = threading.Thread(target=run, daemon=True); self.worker.start()

    def _comb_plot(self):
        import numpy as np
        a = self._comb_acc
        if not a["wind"]: return
        self._comb_fig.clear(); ax = self._comb_fig.add_subplot(111)
        sc = ax.scatter(a["wind"], a["pitch"], c=a["sat"], cmap="turbo", s=7, alpha=0.5, vmin=0, vmax=100)
        self._comb_fig.colorbar(sc, ax=ax, label="gimbal saturation %")
        ax.set_xlabel("wind (m/s)"); ax.set_ylabel("boost-phase peak pitch (deg)")
        ax.set_title(f"Closed-loop TVC over random conditions, {len(a['wind']):,} flights")
        ax.grid(alpha=0.3); self._comb_fig.tight_layout(); self._comb_canvas.draw()

    # =============================================================== Static Motor Tester tab
    def _embed(self, holder, fig):
        for w in holder.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=holder)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        return canvas

    def _build_motor_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Static Motor Tester")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Static-stand motor tester", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="Pick a motor; see its thrust curve and the\naxial load-cell trace the stand would log.",
                  foreground="#667").pack(anchor="w", pady=(0, 6))
        row = ttk.Frame(left); row.pack(fill="x", pady=3)
        ttk.Label(row, text="Motor", width=12).pack(side="left")
        self.mt_motor = tk.StringVar(value="Estes F15")
        ttk.Combobox(row, textvariable=self.mt_motor, state="readonly", width=16,
                     values=bench_sim.MOTOR_NAMES).pack(side="left")
        row2 = ttk.Frame(left); row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Axial cell (kg)", width=12).pack(side="left")
        self.mt_cell = tk.StringVar(value="5")
        ttk.Combobox(row2, textvariable=self.mt_cell, state="readonly", width=16,
                     values=["1", "5", "10", "20"]).pack(side="left")
        self.mt_motor.trace_add("write", lambda *a: self._motor_compute())
        self.mt_cell.trace_add("write", lambda *a: self._motor_compute())
        ttk.Button(left, text="Simulate ▶", command=self._motor_compute).pack(anchor="w", pady=6)
        self.mt_txt = tk.Text(left, width=34, height=10, wrap="word"); self.mt_txt.pack(fill="x", pady=4)
        self._mt_holder = ttk.Frame(f); self._mt_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.after(250, self._motor_compute)

    def _motor_compute(self):
        try:
            name = self.mt_motor.get(); cell = float(self.mt_cell.get())
            fig = bench_sim.make_motor_figure(name, cell_kg=cell)
            self._embed(self._mt_holder, fig)
            s = bench_sim.motor_stats(name); ts, true, rd, st, info = bench_sim.static_stand_trace(name, cell_kg=cell)
            self.mt_txt.delete("1.0", "end")
            self.mt_txt.insert("end", f"{name} ({s['cls']}-class)\n"
                f" total impulse : {s['It']:.1f} N·s\n burn time : {s['tb']:.2f} s\n"
                f" avg thrust : {s['avg']:.1f} N\n peak thrust : {s['peak']:.1f} N\n"
                f" {cell:.0f} kg cell FS: {info['cell_fs_N']:.0f} N ({info['headroom']:.1f}× peak)\n"
                + (" ⚠ pick a larger cell, under-ranged!\n" if info['headroom'] < 1.05 else " cell headroom OK\n"))
        except Exception as e:
            messagebox.showerror("Motor tester", repr(e))

    # =============================================================== Jetvane Suitability tab
    def _build_jetvane_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Jetvane Suitability")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Jetvane TVC suitability", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="Side force, axial loss, and thermal survival\nfor a jetvane vs the servo gimbal.",
                  foreground="#667").pack(anchor="w", pady=(0, 6))
        def combo(label, var, values, w=18):
            r = ttk.Frame(left); r.pack(fill="x", pady=3)
            ttk.Label(r, text=label, width=13).pack(side="left")
            cb = ttk.Combobox(r, textvariable=var, state="readonly", width=w, values=values); cb.pack(side="left")
            var.trace_add("write", lambda *a: self._jetvane_compute())
        self.jv_motor = tk.StringVar(value="Estes F15")
        self.jv_mat = tk.StringVar(value="Graphite")
        self.jv_exhaust = tk.StringVar(value="Estes BP (F15)")
        combo("Motor", self.jv_motor, bench_sim.MOTOR_NAMES)
        combo("Vane material", self.jv_mat, list(bench_sim.VANE_MAT))
        combo("Exhaust", self.jv_exhaust, list(bench_sim.EXHAUST))
        r = ttk.Frame(left); r.pack(fill="x", pady=3)
        ttk.Label(r, text="Max deflection °", width=13).pack(side="left")
        self.jv_defl = tk.DoubleVar(value=15.0)
        ttk.Scale(r, from_=5, to=25, variable=self.jv_defl, orient="horizontal",
                  command=lambda *_a: self._jetvane_compute()).pack(side="left", fill="x", expand=True)
        self.jv_txt = tk.Text(left, width=36, height=12, wrap="word"); self.jv_txt.pack(fill="x", pady=6)
        self._jv_holder = ttk.Frame(f); self._jv_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.after(300, self._jetvane_compute)

    def _jetvane_compute(self):
        try:
            fig = bench_sim.make_jetvane_figure(self.jv_motor.get(), self.jv_mat.get(),
                                                self.jv_exhaust.get(), float(self.jv_defl.get()))
            self._embed(self._jv_holder, fig)
            r = bench_sim.jetvane_analysis(self.jv_motor.get(), self.jv_mat.get(),
                                           self.jv_exhaust.get(), float(self.jv_defl.get()))
            self.jv_txt.delete("1.0", "end"); self.jv_txt.insert("end", r["verdict"])
        except Exception as e:
            messagebox.showerror("Jetvane", repr(e))

    # =============================================================== Ground TVC Test + PID tab
    def _build_groundtvc_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Ground TVC + PID")
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=6)
        ttk.Label(left, text="Ground TVC balance + PID", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="3-axis thrust-vector balance reading as the\nservo gimbals under the firmware PID.",
                  foreground="#667").pack(anchor="w", pady=(0, 6))
        r = ttk.Frame(left); r.pack(fill="x", pady=3)
        ttk.Label(r, text="Motor", width=12).pack(side="left")
        self.gt_motor = tk.StringVar(value="Estes F15")
        ttk.Combobox(r, textvariable=self.gt_motor, state="readonly", width=16,
                     values=bench_sim.MOTOR_NAMES).pack(side="left")
        r2 = ttk.Frame(left); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="Scenario", width=12).pack(side="left")
        self.gt_scn = tk.StringVar(value="Step to 5°, then hold")
        ttk.Combobox(r2, textvariable=self.gt_scn, state="readonly", width=22,
                     values=["Step to 5°, then hold", "Sweep ±deflection",
                             "PID reject 3° mount tilt"]).pack(side="left")
        self.gt_vars = {}
        def slider(key, label, lo, hi, init, res=0.01):
            rr = ttk.Frame(left); rr.pack(fill="x", pady=2)
            ttk.Label(rr, text=label, width=12).pack(side="left")
            var = tk.DoubleVar(value=init); self.gt_vars[key] = var
            ttk.Scale(rr, from_=lo, to=hi, variable=var, orient="horizontal",
                      command=lambda *_a: self._groundtvc_compute()).pack(side="left", fill="x", expand=True)
        slider("kp", "Kp", 0.0, 1.0, core.KP); slider("ki", "Ki", 0.0, 2.0, core.KI)
        slider("kd", "Kd", 0.0, 1.0, core.KD); slider("gim", "Gimbal °", 1.0, 10.0, 8.0, res=0.1)
        slider("tau", "Servo τ (s)", 0.01, 0.12, 0.04, res=0.005)
        for v in (self.gt_motor, self.gt_scn):
            v.trace_add("write", lambda *a: self._groundtvc_compute())
        self.gt_txt = tk.Text(left, width=34, height=8, wrap="word"); self.gt_txt.pack(fill="x", pady=6)
        self._gt_holder = ttk.Frame(f); self._gt_holder.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.after(350, self._groundtvc_compute)

    def _groundtvc_compute(self):
        try:
            g = self.gt_vars
            fig, m = bench_sim.make_ground_tvc_figure(
                self.gt_motor.get(), kp=g["kp"].get(), ki=g["ki"].get(), kd=g["kd"].get(),
                gimbal_deg=g["gim"].get(), scenario=self.gt_scn.get(), tau_servo=g["tau"].get())
            self._embed(self._gt_holder, fig)
            self.gt_txt.delete("1.0", "end")
            self.gt_txt.insert("end",
                f"peak axial Fz : {m['peak_axial_N']:.1f} N ({m['ax_headroom']:.1f}× cell)\n"
                f"peak side Fx : {m['peak_side_N']:.2f} N ({m['lat_headroom']:.1f}× cell)\n"
                f"max gimbal : {m['max_gimbal_deg']:.1f}°\n"
                f"saturation : {m['sat_pct']:.1f}%\n"
                f"motor : {m['motor']['name']} ({m['motor']['It']:.0f} N·s)\n")
        except Exception as e:
            messagebox.showerror("Ground TVC", repr(e))

    # =============================================================== engines tab
    def _build_engines_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="Project Engines")
        ttk.Label(f, text="Run a single-flight / analysis engine. Output captured below; "
                          "plots land in Simulations/plots*/.").pack(anchor="w", padx=8, pady=6)
        self.eng_var = tk.StringVar(value=ENGINES[0][1])
        grid = ttk.Frame(f); grid.pack(fill="x", padx=8)
        for i, (lbl, script) in enumerate(ENGINES):
            ttk.Radiobutton(grid, text=lbl, variable=self.eng_var, value=script).grid(
                row=i // 2, column=i % 2, sticky="w", padx=6, pady=2)
        bb = ttk.Frame(f); bb.pack(fill="x", padx=8, pady=6)
        ttk.Button(bb, text="Run engine", command=self._run_engine).pack(side="left")
        ttk.Button(bb, text="Open plots folder", command=self._open_plots).pack(side="left", padx=6)
        self.eng_log = tk.Text(f, height=22, wrap="word"); self.eng_log.pack(fill="both", expand=True, padx=8, pady=6)

    def _run_engine(self):
        script = os.path.join(SIM_DIR, self.eng_var.get())
        if not os.path.exists(script):
            self.eng_log.insert("end", f"[not found] {script}\n"); return
        tag = "_" + time.strftime("%Y%m%d_%H%M%S") # arc-sim style: each run -> its own folder
        self.eng_log.insert("end", f"\n$ WYVERN_RUN_TAG={tag} python3 {os.path.basename(script)}\n"
                                   f" (outputs -> Simulations/plots*{tag}/)\n"); self.eng_log.see("end")
        def run():
            try:
                env = dict(os.environ, WYVERN_RUN_TAG=tag)
                p = subprocess.run([sys.executable, script], cwd=SIM_DIR, env=env,
                                   capture_output=True, text=True, timeout=1800)
                out = (p.stdout or "") + (p.stderr or "")
            except Exception as e:
                out = repr(e)
            self.q.put(("eng", out))
        threading.Thread(target=run, daemon=True).start()

    def _open_plots(self):
        # each run writes a timestamped plots*_<tag>/ folder; open Simulations/ so they're all visible
        self._os_open(SIM_DIR)

    @staticmethod
    def _os_open(path):
        try:
            if sys.platform == "darwin": subprocess.Popen(["open", path])
            elif os.name == "nt": os.startfile(path) # noqa
            else: subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    # =============================================================== about tab
    def _build_about_tab(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="About")
        txt = tk.Text(f, wrap="word"); txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("end",
            "GTR70E WYVERN, Simulation & Dataset Suite\n"
            "==========================================\n\n"
            "Canonical vehicle (matches we4_flightsim.py):\n"
            f" Liftoff {core.M_LIFT*1000:.0f} g / dry {core.M_DRY*1000:.0f} g · Estes F15-4 (flight)\n"
            f" Apogee ~98.9 m / 324 ft @ ~6.27 s · deploy t={core.DEPLOY_T:.2f} s\n"
            f" Fins 4x72 mm PLA · CG {core.CG*100:.1f} cm / CP {core.XCP*100:.1f} cm\n\n"
            "Datasets: outcomes (1 row/flight), timeseries (ML), tvc (control perf). Parquet or gzip-CSV,\n"
            "streamed in chunks (flat memory, no row cap).\n\n"
            "Headless CLI (run from wyvern_datagen/):\n"
            " /opt/homebrew/bin/python3 datagen.py outcomes --n 2000000 --out datasets/out.parquet\n"
            " /opt/homebrew/bin/python3 datagen.py timeseries --flights 50000 --out datasets/ts.parquet\n"
            " /opt/homebrew/bin/python3 datagen.py tvc --n 1000000 --out datasets/tvc.parquet\n\n"
            "Shortcuts: F11 fullscreen · Esc exit fullscreen.\n")
        txt.config(state="disabled")

    # =============================================================== event pump
    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self._logln(payload)
                elif kind == "progress":
                    d, t, r, rate = payload
                    self.pbar["value"] = 100.0 * d / max(t, 1)
                    self._logln(f" {100.0*d/max(t,1):5.1f}% flights={d:,}/{t:,} rows={r:,} {rate:,.0f}/s",
                               replace_last=True)
                elif kind == "done":
                    self.last_output = payload["path"]
                    self._logln(f"DONE {payload['rows']:,} rows -> {payload['path']} "
                               f"({payload['fmt']}, {payload['seconds']}s). "
                               f"Use 'Load last generated' in Plots & Analysis.")
                    self.go_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
                elif kind == "error":
                    self._logln("ERROR: " + payload); self.ds_lbl.config(text="(load failed)")
                    self.go_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
                elif kind == "eng":
                    self.eng_log.insert("end", payload + "\n"); self.eng_log.see("end")
                elif kind == "dataset":
                    path, data, cols, ntot, nload = payload
                    self.dataset = data; self.dataset_cols = cols
                    numc = analysis.numeric_cols(data)
                    self.xcol.config(values=numc); self.ycol.config(values=numc)
                    if numc:
                        self.xcol.set("apogee_m" if "apogee_m" in numc else numc[0])
                        self.ycol.set("wind_ms" if "wind_ms" in numc else numc[min(1, len(numc)-1)])
                    self.ds_lbl.config(text=f"{os.path.basename(path)}, {ntot:,} rows"
                                           + (f" ({nload:,} loaded)" if nload != ntot else "") + f", {len(cols)} cols")
                    self.nb.select(1)
                elif kind == "viewer":
                    r = payload
                    self._vw_cols = r["columns"]; self._vw_rows = list(r["rows"])
                    self._vw_numeric = r["numeric"]; self._vw_total = r["total"]
                    self._vw_sort = (None, False)
                    a = r["_start"]; b = a + len(self._vw_rows)
                    tot = f"{r['total']:,}" if r["total"] is not None else "? (CSV)"
                    fmt = "Parquet" if r["_path"].endswith(".parquet") else "CSV"
                    self.vw_info.config(text=f"{fmt} · {tot} rows × {len(self._vw_cols)} cols · "
                                            f"showing {a:,}–{max(a, b-1):,}")
                    self._viewer_populate()
                elif kind == "comb_prog":
                    d, t, rows, rate = payload
                    self.comb_pbar["value"] = 100.0 * d / max(t, 1)
                    eta = (t - d) / max(rate, 1e-9)
                    self.comb_status.insert("end", f" {100.0*d/max(t,1):5.1f}% {d:,}/{t:,} flights · "
                                           f"{rows:,} log rows · {rate:.1f}/s · ETA {eta/60:.1f} min\n")
                    self.comb_status.see("end")
                elif kind == "comb_sample":
                    for srow in payload:
                        self._comb_acc["wind"].append(srow["wind_ms"])
                        self._comb_acc["pitch"].append(srow["peak_pitch_boost_deg"])
                        self._comb_acc["apogee"].append(srow["apogee_true_m"])
                        self._comb_acc["sat"].append(srow["gimbal_sat_boost_pct"])
                    self._comb_plot()
                elif kind == "comb_done":
                    r = payload
                    self.last_output = r["summary_path"]
                    self.comb_status.insert("end",
                        f"DONE {r['flights']:,} flights · {r['rows']:,} log rows · {r['seconds']}s\n"
                        f" summary → {os.path.basename(r['summary_path'])}\n"
                        f" log → {os.path.basename(r['log_path'])}\n"
                        f"'Load last generated' in Plots & Analysis opens the summary.")
                    self.comb_status.see("end")
                    self.comb_btn.config(state="normal"); self.comb_cancel.config(state="disabled")
                elif kind == "sil":
                    r = payload; s = r["summary"]
                    self._sil_plot(r)
                    self.sil_summary.delete("1.0", "end")
                    self.sil_summary.insert("end",
                        f"apogee {s['apogee_true_m']} m (baro {s['apogee_baro_m']}, err {s['apogee_err_m']} m)\n"
                        f"boost pitch {s['peak_pitch_boost_deg']}° · gimbal RMS {s['rms_gimbal_boost_deg']}°\n"
                        f"coast nose-over {s['peak_pitch_coast_deg']}°\n"
                        f"touchdown {s['touchdown_v_ms']} m/s · flight {s['flight_time_s']} s\n"
                        f"states OK · landed={s['landed']}")
                    self._sil_tel_buf = r["telemetry"]; self._sil_tel_i = 0
                    self.sil_telem.delete("1.0", "end"); self._sil_stream()
                    self.sil_btn.config(state="normal")
                elif kind == "autotune":
                    best, fw = payload; self._autotune_best = best
                    imp = 100.0 * (fw[0] - best[0]) / fw[0]
                    self.pid_metrics.delete("1.0", "end")
                    self.pid_metrics.insert("end",
                        f"Auto-tune (robust, winds 3-12 m/s):\n"
                        f"best Kp={best[1]:.3f} Ki={best[2]:.3f} Kd={best[3]:.3f} cost {best[0]:.2f}\n"
                        f"firmware {core.KP}/{core.KI}/{core.KD} cost {fw[0]:.2f} ({imp:+.1f}%)\n\n"
                        f"Note: grid-best often drops Ki; firmware keeps integral for steady-bias\n"
                        f"rejection (see PID_AUTOTUNE_REPORT.md). 'Apply best' loads it into the sliders.")
                    self.pid_autotune_btn.config(state="normal")
                elif kind == "nominal":
                    data, apo, apot = payload
                    self.dataset = data; self.dataset_cols = list(data)
                    numc = analysis.numeric_cols(data)
                    self.xcol.config(values=numc); self.ycol.config(values=numc)
                    self.xcol.set("t"); self.ycol.set("z")
                    self.pk_var.set("Scatter")
                    self.ds_lbl.config(text=f"nominal flight, apogee {apo:.1f} m @ {apot:.2f} s")
                    self.nb.select(1); self._plot()
        except queue.Empty:
            pass
        self.after(120, self._drain_queue)

    def _logln(self, msg, replace_last=False):
        if replace_last:
            try: self.log.delete("end-2l", "end-1l")
            except Exception: pass
        self.log.insert("end", msg + "\n"); self.log.see("end")


def main():
    Suite().mainloop()


if __name__ == "__main__":
    main()
