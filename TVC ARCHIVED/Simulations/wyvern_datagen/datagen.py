#!/usr/bin/env python3
"""
GTR70E WYVERN, Monte-Carlo dataset generator.

Streams millions of datapoints to disk in chunks so memory stays flat regardless of dataset size.
Three dataset types (all selectable from the GUI or CLI):

  outcomes : one row per flight (sampled atmosphere -> apogee, maxQ, maxMach, drift, landing, ...)
  timeseries: many rows per flight (t, x, z, v, a, Mach, q + conditions) -- the big ML dataset
  tvc : one row per flight (peak pitch error, RMS gimbal, saturation %, settle time)

Format is chosen automatically: Parquet when pyarrow is present (compact, columnar, ideal for the
huge time-series set), otherwise gzip-CSV. Override with fmt="csv"/"parquet".

CLI (run from this folder; use the interpreter that has numpy/pyarrow, e.g. /opt/homebrew/bin/python3):
  /opt/homebrew/bin/python3 datagen.py outcomes --n 2000000 --out datasets/outcomes.parquet
  /opt/homebrew/bin/python3 datagen.py timeseries --flights 50000 --stride 10 --out datasets/timeseries.parquet
  /opt/homebrew/bin/python3 datagen.py tvc --n 1000000 --out datasets/tvc.parquet
  /opt/homebrew/bin/python3 datagen.py flightlog --flights 2000 --out datasets/sil.parquet (closed-loop SIL)
"""
import os, sys, time, argparse, gzip
import numpy as np

try:
    import core, fc_sil # when run as a script from inside the package dir
except ImportError:
    from . import core, fc_sil # when imported as wyvern_datagen.*

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAVE_PARQUET = True
except Exception:
    HAVE_PARQUET = False


# ---------------------------------------------------------------- column orders
# Column sets widened in the 2026-08 fidelity revision: the sampled vehicle build dispersion
# (mass/CG/Cd/impulse/misalignment) and the wind-shear exponent are now first-class columns, so a
# downstream model can condition on them instead of treating them as unobserved noise. Rail-exit
# speed, max-q altitude and the reconstructed coast Cd are added because they are the quantities
# the flight-telemetry comparison in Proposal RQ3 is actually scored against.
OUTCOME_COLS = ["flight_id", "wind_ms", "wind_dir_deg", "turb_pct", "shear_alpha", "temp_C",
                "pressure_mbar", "launch_tilt_deg", "site_alt_m",
                "m_lift_kg", "cg_m", "cd_scale", "impulse_scale", "misalign_deg",
                "static_margin_cal",
                "apogee_m", "apogee_ft", "apogee_t",
                "max_speed_ms", "max_mach", "max_q_pa", "max_q_alt_m", "max_accel_g",
                "rail_exit_speed_ms", "rail_exit_t_s", "burnout_alt_m", "burnout_speed_ms",
                "coast_cd_eff", "deploy_alt_m", "deploy_vspeed_ms", "descent_rate_ms",
                "flight_time_s", "landing_x_m", "drift_from_pad_m"]
TVC_COLS = ["flight_id", "wind_ms", "turb_pct", "shear_alpha", "temp_C", "pressure_mbar",
            "launch_tilt_deg", "cg_m", "static_margin_cal", "misalign_deg",
            "peak_pitch_err_deg", "rms_pitch_err_deg", "rms_gimbal_deg",
            "gimbal_saturation_pct", "peak_gimbal_rate_dps", "settle_time_s"]
TRACE_COLS = ["flight_id", "t", "x", "z", "vx", "vz", "accel_g", "mach", "q", "rho",
              "wind_local_ms", "wind_ms", "turb_pct", "shear_alpha", "temp_C", "pressure_mbar",
              "site_alt_m", "m_lift_kg", "cd_scale"]
FLIGHTLOG_COLS = ["flight_id", "t_s", "state_id", "alt_m", "vz_ms", "pitch_deg", "gimbal_deg",
                  "baro_m", "batt_v", "wind_ms", "turb_pct", "temp_C"]
COMBINED_SUMMARY_COLS = ["flight_id", "wind_ms", "turb_pct", "temp_C", "apogee_true_m", "apogee_baro_m",
                         "peak_pitch_boost_deg", "rms_gimbal_boost_deg", "gimbal_sat_boost_pct",
                         "touchdown_v_ms", "deployed"]


def _default_fmt(fmt):
    if fmt in ("csv", "parquet"):
        return fmt
    return "parquet" if HAVE_PARQUET else "csv"


# Hard project rule: no single file in this repository may exceed 100 MB. GitHub also hard-blocks
# files >= 100 MiB. Cap every generated file at 80 MiB, which leaves headroom for the row-group
# footer that Parquet writes on close (the size estimator below works off an observed bytes/row
# average and can undershoot on the final chunk). Files that would exceed this are split into
# `..._part001.parquet`, `..._part002.parquet`, etc.
MAX_FILE_BYTES = 80 * 1024 * 1024


def _part_path(base_path, part):
    """base_path with a _partNNN tag inserted before the extension (handles .csv.gz too)."""
    if part == 1:
        return base_path
    root, ext = os.path.splitext(base_path)
    if ext == ".gz":
        root, ext2 = os.path.splitext(root)
        ext = ext2 + ext
    return f"{root}_part{part:03d}{ext}"


# ---------------------------------------------------------------- chunk writers
class _Writer:
    """Uniform chunk writer: Parquet (pyarrow) or gzip-CSV, chosen by extension/format.

    Auto-rotates to a new numbered part file whenever the next chunk would push the current
    file past `max_bytes` (default MAX_FILE_BYTES), so no single output file ever exceeds the
    cap. `self.paths` accumulates every part written; `self.path` is always the current one."""
    def __init__(self, path, cols, fmt, max_bytes=MAX_FILE_BYTES):
        self.cols = cols; self.fmt = fmt; self.base_path = path
        self.max_bytes = max_bytes
        self._part = 1
        self.paths = []
        self._rows_since_open = 0
        self._open_part()

    def _open_part(self):
        path = _part_path(self.base_path, self._part)
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        self.path = path
        self.paths.append(path)
        self._rows_since_open = 0
        if self.fmt == "parquet":
            self._pw = None
        else:
            self._fh = gzip.open(path, "wt") if path.endswith(".gz") else open(path, "w")
            self._fh.write(",".join(self.cols) + "\n")

    def _close_part(self):
        if self.fmt == "parquet":
            if self._pw is not None: self._pw.close()
        else:
            self._fh.close()

    def _current_size(self):
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def _estimate_next_bytes(self, n_rows):
        # Use the observed avg bytes/row for the current part once we have data; otherwise fall
        # back to a conservative per-format guess so the very first chunk can't blow past the cap.
        cur_size = self._current_size()
        if self._rows_since_open > 0 and cur_size > 0:
            avg = cur_size / self._rows_since_open
        else:
            avg = 300.0 if self.fmt == "parquet" else 80.0 # bytes/row, conservative
        return cur_size + avg * n_rows

    def write(self, coldict):
        n_rows = len(next(iter(coldict.values())))
        if self.max_bytes and self._rows_since_open > 0:
            if self._estimate_next_bytes(n_rows) >= self.max_bytes:
                self._close_part()
                self._part += 1
                self._open_part()
        if self.fmt == "parquet":
            table = pa.table({c: np.asarray(coldict[c]) for c in self.cols})
            if self._pw is None:
                self._pw = pq.ParquetWriter(self.path, table.schema, compression="snappy")
            self._pw.write_table(table)
        else:
            arr = np.column_stack([np.asarray(coldict[c], dtype=float) for c in self.cols])
            np.savetxt(self._fh, arr, fmt="%.6g", delimiter=",")
            self._fh.flush()
        self._rows_since_open += n_rows

    def close(self):
        self._close_part()


def _resolve_path(path, fmt):
    root, ext = os.path.splitext(path)
    if fmt == "parquet" and ext != ".parquet":
        return root + ".parquet"
    if fmt == "csv" and ext not in (".csv", ".gz"):
        return root + ".csv.gz"
    return path


def _timestamped(path):
    """Insert a _YYYYMMDD_HHMMSS stamp before the extension so every run writes a new file
    (arc-sim style, never overwrite). Handles the double extension .csv.gz."""
    import datetime
    root, ext = os.path.splitext(path)
    if ext == ".gz": # .csv.gz -> peel both
        root, ext2 = os.path.splitext(root); ext = ext2 + ext
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{root}_{ts}{ext}"


# ---------------------------------------------------------------- estimators
def estimate(kind, n=None, flights=None, stride=10, dt=0.002):
    """Return (n_rows, note) preview for the GUI, before committing to a run."""
    if kind == "timeseries":
        pts = int(np.ceil(core.DEPLOY_T / dt / max(stride, 1))) + 1
        rows = int(flights) * pts
        return rows, f"{flights:,} flights x ~{pts} states = {rows:,} rows"
    return int(n), f"{int(n):,} flights = {int(n):,} rows"


# ---------------------------------------------------------------- generators
def _emit(progress_cb, done, total, rows, t0):
    if progress_cb:
        dtm = max(time.time() - t0, 1e-9)
        progress_cb(done, total, rows, rows / dtm)


def generate_outcomes(n_total, out, fmt="auto", chunk=100_000, seed=0, envelope=None,
                      dt=0.002, timestamp=True, progress_cb=None, cancel_cb=None,
                      max_bytes=MAX_FILE_BYTES):
    fmt = _default_fmt(fmt); out = _resolve_path(out, fmt)
    if timestamp: out = _timestamped(out)
    w = _Writer(out, OUTCOME_COLS, fmt, max_bytes=max_bytes); t0 = time.time(); done = 0; rows = 0
    fid0 = 0
    while done < n_total:
        if cancel_cb and cancel_cb(): break
        m = min(chunk, n_total - done)
        o = core.simulate_outcomes(m, seed=seed + done, envelope=envelope, dt=dt)
        o["flight_id"] = np.arange(fid0, fid0 + m)
        w.write(o); rows += m; done += m; fid0 += m
        _emit(progress_cb, done, n_total, rows, t0)
    w.close()
    return dict(path=w.paths[0], paths=w.paths, parts=len(w.paths), rows=rows, fmt=fmt,
                seconds=round(time.time() - t0, 2))


def generate_tvc(n_total, out, fmt="auto", chunk=100_000, seed=0, envelope=None,
                 dt=0.001, timestamp=True, progress_cb=None, cancel_cb=None,
                 max_bytes=MAX_FILE_BYTES):
    fmt = _default_fmt(fmt); out = _resolve_path(out, fmt)
    if timestamp: out = _timestamped(out)
    w = _Writer(out, TVC_COLS, fmt, max_bytes=max_bytes); t0 = time.time(); done = 0; rows = 0; fid0 = 0
    while done < n_total:
        if cancel_cb and cancel_cb(): break
        m = min(chunk, n_total - done)
        o = core.simulate_tvc(m, seed=seed + done, envelope=envelope, dt=dt)
        o["flight_id"] = np.arange(fid0, fid0 + m)
        w.write(o); rows += m; done += m; fid0 += m
        _emit(progress_cb, done, n_total, rows, t0)
    w.close()
    return dict(path=w.paths[0], paths=w.paths, parts=len(w.paths), rows=rows, fmt=fmt,
                seconds=round(time.time() - t0, 2))


def generate_timeseries(n_flights, out, fmt="auto", flight_chunk=2000, stride=10, seed=0,
                        envelope=None, dt=0.002, timestamp=True, progress_cb=None, cancel_cb=None,
                        max_bytes=MAX_FILE_BYTES):
    fmt = _default_fmt(fmt); out = _resolve_path(out, fmt)
    if timestamp: out = _timestamped(out)
    w = _Writer(out, TRACE_COLS, fmt, max_bytes=max_bytes); t0 = time.time(); done = 0; rows = 0; fid0 = 0
    total_rows, _ = estimate("timeseries", flights=n_flights, stride=stride, dt=dt)
    while done < n_flights:
        if cancel_cb and cancel_cb(): break
        m = min(flight_chunk, n_flights - done)
        out_o, tr, cond = core.simulate_trace(m, seed=seed + done, envelope=envelope,
                                              dt=dt, trace_stride=stride)
        nsp = tr["t"].shape[0] # states per flight in this chunk
        # flatten (nsp, m) -> (nsp*m,), flight-major
        fid = np.repeat(np.arange(fid0, fid0 + m), nsp)
        col = {"flight_id": fid}
        for k in ("t", "x", "z", "vx", "vz", "accel_g", "mach", "q", "rho", "wind_local_ms"):
            col[k] = tr[k].T.reshape(-1) # (m, nsp) -> flat
        for k in ("wind_ms", "turb_pct", "shear_alpha", "temp_C", "pressure_mbar",
                  "site_alt_m", "m_lift_kg", "cd_scale"):
            col[k] = np.repeat(cond[k], nsp)
        w.write(col); rows += fid.size; done += m; fid0 += m
        _emit(progress_cb, done, n_flights, rows, t0)
    w.close()
    return dict(path=w.paths[0], paths=w.paths, parts=len(w.paths), rows=rows, fmt=fmt,
                seconds=round(time.time() - t0, 2), approx_total_rows=total_rows)


def generate_flightlog(n_flights, out, fmt="auto", flight_chunk=200, seed=0, envelope=None,
                       dt=0.004, t_max=9.0, log_hz=50, timestamp=True,
                       progress_cb=None, cancel_cb=None, max_bytes=MAX_FILE_BYTES):
    """Closed-loop SIL flight logs (state machine + sensor noise + PID), one flight at a time.
    Sequential (~5-15 flights/s), realism over raw count. Truncates at t_max (default 9 s, through
    deploy + chute-open) to focus on the controlled phase."""
    fmt = _default_fmt(fmt); out = _resolve_path(out, fmt)
    if timestamp: out = _timestamped(out)
    w = _Writer(out, FLIGHTLOG_COLS, fmt, max_bytes=max_bytes); t0 = time.time(); rows = 0; done = 0
    e = dict(core.ENVELOPE);
    if envelope: e.update(envelope)
    rng = np.random.default_rng(seed)
    buf = {c: [] for c in FLIGHTLOG_COLS}

    def flush():
        nonlocal rows
        if buf["flight_id"]:
            w.write({c: np.asarray(buf[c], dtype=float) for c in FLIGHTLOG_COLS}); rows += len(buf["flight_id"])
            for c in FLIGHTLOG_COLS: buf[c].clear()

    for fid in range(n_flights):
        if cancel_cb and cancel_cb(): break
        u = lambda k: rng.uniform(*e[k]) if e[k][1] > e[k][0] else e[k][0]
        wind = u("wind_ms"); turb = u("turb_pct"); temp = u("temp_C")
        r = fc_sil.run_sil(wind_ms=wind, turb_pct=turb, temp_C=temp,
                           pressure_mbar=u("pressure_mbar"), launch_tilt_deg=u("launch_tilt_deg"),
                           seed=seed + fid, dt=dt, log_hz=log_hz, t_max=t_max)
        for (ts, state, alt, vzz, pitch, gmbl, baro, batt) in r["logs"]:
            buf["flight_id"].append(fid); buf["t_s"].append(ts)
            buf["state_id"].append(fc_sil.STATES.index(state)); buf["alt_m"].append(alt)
            buf["vz_ms"].append(vzz); buf["pitch_deg"].append(pitch); buf["gimbal_deg"].append(gmbl)
            buf["baro_m"].append(baro); buf["batt_v"].append(batt)
            buf["wind_ms"].append(wind); buf["turb_pct"].append(turb); buf["temp_C"].append(temp)
        done += 1
        if done % flight_chunk == 0:
            flush(); _emit(progress_cb, done, n_flights, rows, t0)
    flush(); _emit(progress_cb, done, n_flights, rows, t0)
    w.close()
    return dict(path=w.paths[0], paths=w.paths, parts=len(w.paths), rows=rows, fmt=fmt,
                seconds=round(time.time() - t0, 2))


def generate_combined(n_flights, out, fmt="auto", seed=0, envelope=None, gimbal_deg=8.0,
                      dt=0.004, t_max=9.0, log_flight_chunk=200, sample_every=250, timestamp=True,
                      progress_cb=None, sample_cb=None, cancel_cb=None, max_bytes=MAX_FILE_BYTES):
    """Super-combined mode: live closed-loop SIL over N random flights (default use: 25,000). Writes
    BOTH the full time-series log (`*_log`) and a compact per-flight summary (`*_flights`), each
    timestamped. progress_cb(done,total,rows,rate); sample_cb(list_of_summary_dicts) feeds live viz."""
    fmt = _default_fmt(fmt)
    root, ext = os.path.splitext(_resolve_path(out, fmt))
    if ext == ".gz":
        root, e2 = os.path.splitext(root); ext = e2 + ext
    import datetime
    ts = ("_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")) if timestamp else ""
    logpath = f"{root}_log{ts}{ext}"; sumpath = f"{root}_flights{ts}{ext}"
    wl = _Writer(logpath, FLIGHTLOG_COLS, fmt, max_bytes=max_bytes)
    ws = _Writer(sumpath, COMBINED_SUMMARY_COLS, fmt, max_bytes=max_bytes)
    t0 = time.time(); rows = 0; done = 0
    e = dict(core.ENVELOPE)
    if envelope: e.update(envelope)
    rng = np.random.default_rng(seed)
    lbuf = {c: [] for c in FLIGHTLOG_COLS}; sbuf = {c: [] for c in COMBINED_SUMMARY_COLS}; recent = []

    def flush_log():
        nonlocal rows
        if lbuf["flight_id"]:
            wl.write({c: np.asarray(lbuf[c], dtype=float) for c in FLIGHTLOG_COLS})
            rows += len(lbuf["flight_id"])
            for c in FLIGHTLOG_COLS: lbuf[c].clear()

    for fid in range(n_flights):
        if cancel_cb and cancel_cb(): break
        u = lambda k: rng.uniform(*e[k]) if e[k][1] > e[k][0] else e[k][0]
        wind = u("wind_ms"); turb = u("turb_pct"); temp = u("temp_C")
        r = fc_sil.run_sil(wind_ms=wind, turb_pct=turb, temp_C=temp, pressure_mbar=u("pressure_mbar"),
                           launch_tilt_deg=u("launch_tilt_deg"), gimbal_deg=gimbal_deg,
                           seed=seed + fid, dt=dt, log_hz=50, t_max=t_max)
        s = r["summary"]
        for (tsv, state, alt, vzz, pitch, gmbl, baro, batt) in r["logs"]:
            lbuf["flight_id"].append(fid); lbuf["t_s"].append(tsv)
            lbuf["state_id"].append(fc_sil.STATES.index(state)); lbuf["alt_m"].append(alt)
            lbuf["vz_ms"].append(vzz); lbuf["pitch_deg"].append(pitch); lbuf["gimbal_deg"].append(gmbl)
            lbuf["baro_m"].append(baro); lbuf["batt_v"].append(batt)
            lbuf["wind_ms"].append(wind); lbuf["turb_pct"].append(turb); lbuf["temp_C"].append(temp)
        srow = dict(flight_id=fid, wind_ms=wind, turb_pct=turb, temp_C=temp,
                    apogee_true_m=s["apogee_true_m"], apogee_baro_m=s["apogee_baro_m"],
                    peak_pitch_boost_deg=s["peak_pitch_boost_deg"], rms_gimbal_boost_deg=s["rms_gimbal_boost_deg"],
                    gimbal_sat_boost_pct=s["gimbal_sat_boost_pct"], touchdown_v_ms=s["touchdown_v_ms"],
                    deployed=1 if s["deployed"] else 0)
        for c in COMBINED_SUMMARY_COLS: sbuf[c].append(srow[c])
        recent.append(srow); done += 1
        if done % log_flight_chunk == 0: flush_log()
        if done % sample_every == 0:
            if progress_cb: progress_cb(done, n_flights, rows + len(lbuf["flight_id"]), done / max(time.time() - t0, 1e-9))
            if sample_cb: sample_cb(recent); recent = []
    flush_log()
    ws.write({c: np.asarray(sbuf[c], dtype=float) for c in COMBINED_SUMMARY_COLS}); ws.close(); wl.close()
    if progress_cb: progress_cb(done, n_flights, rows, done / max(time.time() - t0, 1e-9))
    if sample_cb and recent: sample_cb(recent)
    return dict(log_path=wl.paths[0], log_paths=wl.paths, summary_path=ws.paths[0],
                summary_paths=ws.paths, flights=done, rows=rows, fmt=fmt,
                seconds=round(time.time() - t0, 2))


# ---------------------------------------------------------------- CLI
def _cli_progress(done, total, rows, rate):
    pct = 100.0 * done / max(total, 1)
    sys.stdout.write(f"\r {pct:5.1f}% flights={done:,}/{total:,} rows={rows:,} {rate:,.0f}/s ")
    sys.stdout.flush()


def main(argv=None):
    p = argparse.ArgumentParser(description="GTR70E WYVERN Monte-Carlo dataset generator")
    sub = p.add_subparsers(dest="kind", required=True)
    for k in ("outcomes", "tvc"):
        s = sub.add_parser(k); s.add_argument("--n", type=int, required=True)
        s.add_argument("--out", required=True); s.add_argument("--fmt", default="auto")
        s.add_argument("--chunk", type=int, default=100_000); s.add_argument("--seed", type=int, default=0)
        s.add_argument("--no-timestamp", dest="timestamp", action="store_false",
                       help="overwrite --out instead of writing a new timestamped file")
        s.add_argument("--max-mb", type=float, default=80.0,
                       help="split output into _partNNN files once a file would exceed this size (MiB)")
    st = sub.add_parser("timeseries")
    st.add_argument("--flights", type=int, required=True); st.add_argument("--out", required=True)
    st.add_argument("--stride", type=int, default=10); st.add_argument("--fmt", default="auto")
    st.add_argument("--flight-chunk", type=int, default=2000); st.add_argument("--seed", type=int, default=0)
    st.add_argument("--no-timestamp", dest="timestamp", action="store_false",
                    help="overwrite --out instead of writing a new timestamped file")
    st.add_argument("--max-mb", type=float, default=80.0,
                    help="split output into _partNNN files once a file would exceed this size (MiB)")
    fl = sub.add_parser("flightlog")
    fl.add_argument("--flights", type=int, required=True); fl.add_argument("--out", required=True)
    fl.add_argument("--fmt", default="auto"); fl.add_argument("--seed", type=int, default=0)
    fl.add_argument("--t-max", type=float, default=9.0, dest="t_max")
    fl.add_argument("--no-timestamp", dest="timestamp", action="store_false")
    fl.add_argument("--max-mb", type=float, default=80.0,
                    help="split output into _partNNN files once a file would exceed this size (MiB)")
    cb = sub.add_parser("combined")
    cb.add_argument("--flights", type=int, default=25000); cb.add_argument("--out", required=True)
    cb.add_argument("--fmt", default="auto"); cb.add_argument("--seed", type=int, default=0)
    cb.add_argument("--gimbal", type=float, default=8.0, dest="gimbal_deg")
    cb.add_argument("--no-timestamp", dest="timestamp", action="store_false")
    cb.add_argument("--max-mb", type=float, default=80.0,
                    help="split output into _partNNN files once a file would exceed this size (MiB)")
    a = p.parse_args(argv)
    max_bytes = int(a.max_mb * 1024 * 1024)
    if a.kind == "outcomes":
        r = generate_outcomes(a.n, a.out, a.fmt, a.chunk, a.seed, timestamp=a.timestamp,
                              progress_cb=_cli_progress, max_bytes=max_bytes)
    elif a.kind == "tvc":
        r = generate_tvc(a.n, a.out, a.fmt, a.chunk, a.seed, timestamp=a.timestamp,
                         progress_cb=_cli_progress, max_bytes=max_bytes)
    elif a.kind == "flightlog":
        r = generate_flightlog(a.flights, a.out, a.fmt, seed=a.seed, t_max=a.t_max,
                               timestamp=a.timestamp, progress_cb=_cli_progress, max_bytes=max_bytes)
    elif a.kind == "combined":
        r = generate_combined(a.flights, a.out, a.fmt, seed=a.seed, gimbal_deg=a.gimbal_deg,
                              timestamp=a.timestamp, progress_cb=_cli_progress, max_bytes=max_bytes)
        print(f"\nDONE {r['flights']:,} flights -> log {r['log_paths']} + summary {r['summary_paths']} "
              f"({r['rows']:,} log rows, {r['seconds']}s)")
        return r
    else:
        r = generate_timeseries(a.flights, a.out, a.fmt, a.flight_chunk, a.stride, a.seed,
                                timestamp=a.timestamp, progress_cb=_cli_progress, max_bytes=max_bytes)
    parts_note = f" [{r['parts']} parts]" if r["parts"] > 1 else ""
    print(f"\nDONE {r['rows']:,} rows -> {r['paths']}{parts_note} ({r['fmt']}, {r['seconds']}s, "
          f"{r['rows']/max(r['seconds'],1e-9):,.0f} rows/s)")
    return r


if __name__ == "__main__":
    main()
