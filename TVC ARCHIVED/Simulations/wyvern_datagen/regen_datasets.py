#!/usr/bin/env python3
"""
GTR70E WYVERN, resumable, parallel dataset regeneration driver.

Why this exists: the full Monte-Carlo regeneration is tens of CPU-minutes, which is longer than
any single interactive session or CI step wants to hold open. This driver splits the whole job
into independent, deterministically-seeded shards, runs them across all cores, records what
finished in a state file, and can be re-invoked as many times as needed until the plan is
complete. Re-running after a crash or an interrupt costs only the shards that were in flight.

Each shard writes its own `_partNNN` file, so the 80 MB-per-file project rule is satisfied by
construction rather than by the writer's size estimator having to rotate mid-stream.

Usage:
    python3 regen_datasets.py --budget-s 35 # do ~35 s of work, then exit
    python3 regen_datasets.py --budget-s 35 --status # show remaining work, do nothing
    python3 regen_datasets.py --reset # discard state, re-plan from scratch
"""
import os, sys, json, time, argparse, multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.join(HERE, "datasets")
STATE = os.path.join(DATASETS, "_regen_state.json")

SEED_BASE = 20260801

# ---------------------------------------------------------------- the plan
# Shard sizes are chosen so one shard is ~20-30 s on one core, which keeps the parallel round
# short enough to fit inside a bounded invocation while still amortizing NumPy's per-step
# overhead across a large enough vector to run efficiently.
PLAN = [
    # (kind, shards, per_shard, kwargs)
    ("outcomes", 12, 20_000, dict(dt=0.002)), # 240,000 flights, 34 columns
    ("tvc", 9, 20_000, dict(dt=0.001)), # 180,000 flights, 16 columns
    ("timeseries", 9, 1_500, dict(dt=0.002, stride=10)), # 13,500 flights ~ 5.0 M rows
    # The SIL products are sequential, single-flight, full-firmware runs -- realism over raw
    # count, and now ~3x slower per flight than before because the servo, transport delay and
    # 500 Hz ZOH are modeled explicitly. t_max=12 s carries every flight through
    # ARMED->BOOST->COAST->RECOVER->DESCENT with the chute open and the descent rate settled;
    # the remaining ~15 s of steady parachute ride adds rows but no new dynamics.
    ("flightlog", 10, 60, dict(dt=0.002, t_max=12.0)), # 600 SIL flight logs
    ("combined", 10, 60, dict(dt=0.002, t_max=12.0)), # 600 SIL logs + per-flight summaries
]

BASENAME = {
    "outcomes": "wyvern_outcomes",
    "tvc": "wyvern_tvc",
    "timeseries": "wyvern_timeseries",
    "flightlog": "wyvern_sil_flightlog",
    "combined": "wyvern_combined",
}


def shard_id(kind, i):
    return f"{kind}:{i:03d}"


def build_plan():
    shards = []
    for kind, nsh, per, kw in PLAN:
        for i in range(nsh):
            shards.append(dict(id=shard_id(kind, i), kind=kind, index=i, n=per,
                               seed=SEED_BASE + 100_000 * i + hash(kind) % 1000, kw=kw))
    return shards


def load_state():
    if os.path.exists(STATE):
        with open(STATE) as fh:
            return json.load(fh)
    return dict(done=[], started=None, total_seconds=0.0)


def save_state(st):
    os.makedirs(DATASETS, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=1)
    os.replace(tmp, STATE)


# ---------------------------------------------------------------- worker
def _run_shard(sh):
    """Run one shard in a subprocess. Returns (id, rows, seconds, paths, err)."""
    t0 = time.time()
    try:
        sys.path.insert(0, HERE)
        import datagen
        kind, i, n, kw = sh["kind"], sh["index"], sh["n"], sh["kw"]
        out = os.path.join(DATASETS, f"{BASENAME[kind]}_part{i+1:03d}.parquet")
        common = dict(fmt="parquet", seed=sh["seed"], timestamp=False)
        if kind == "outcomes":
            r = datagen.generate_outcomes(n, out, chunk=n, dt=kw["dt"], **common)
        elif kind == "tvc":
            r = datagen.generate_tvc(n, out, chunk=n, dt=kw["dt"], **common)
        elif kind == "timeseries":
            r = datagen.generate_timeseries(n, out, flight_chunk=min(n, 2000),
                                            stride=kw["stride"], dt=kw["dt"], **common)
        elif kind == "flightlog":
            r = datagen.generate_flightlog(n, out, dt=kw["dt"], t_max=kw["t_max"], **common)
        elif kind == "combined":
            r = datagen.generate_combined(n, out, dt=kw["dt"], t_max=kw["t_max"], **common)
        else:
            raise ValueError(kind)
        paths = r.get("paths") or (r.get("log_paths", []) + r.get("summary_paths", []))
        return (sh["id"], r.get("rows", 0), round(time.time() - t0, 1), paths, None)
    except Exception as e: # a shard failure must not take the whole run down
        import traceback
        return (sh["id"], 0, round(time.time() - t0, 1), [], traceback.format_exc(limit=4))


# ---------------------------------------------------------------- driver
def main(argv=None):
    ap = argparse.ArgumentParser(description="Resumable parallel GTR70E WYVERN dataset regeneration")
    ap.add_argument("--budget-s", type=float, default=35.0,
                    help="approximate wall-clock budget for this invocation")
    ap.add_argument("--workers", type=int, default=3,
                    help="parallel shards per round; the sandbox CPU quota is ~1.5 cores, so 3 is "
                         "the point past which rounds get longer without finishing more work")
    ap.add_argument("--status", action="store_true", help="report progress and exit")
    ap.add_argument("--reset", action="store_true", help="discard state and re-plan")
    a = ap.parse_args(argv)

    if a.reset and os.path.exists(STATE):
        os.remove(STATE)

    plan = build_plan()
    st = load_state()
    done = set(st["done"])
    todo = [s for s in plan if s["id"] not in done]

    by_kind = {}
    for s in plan:
        k = s["kind"]; by_kind.setdefault(k, [0, 0])
        by_kind[k][1] += 1
        if s["id"] in done: by_kind[k][0] += 1
    print(f"plan: {len(done)}/{len(plan)} shards complete "
          f"({st['total_seconds']:.0f} s spent so far)")
    for k, (d, t) in by_kind.items():
        print(f" {k:11} {d:3d}/{t:3d}")
    if a.status or not todo:
        if not todo:
            print("ALL_SHARDS_COMPLETE")
        return 0

    t_start = time.time()
    rounds = 0
    while todo and (time.time() - t_start) < a.budget_s:
        batch = todo[:a.workers]
        with mp.Pool(len(batch)) as pool:
            for sid, rows, secs, paths, err in pool.map(_run_shard, batch):
                if err:
                    print(f" FAIL {sid} after {secs}s\n{err}")
                else:
                    done.add(sid)
                    st["done"] = sorted(done)
                    print(f" ok {sid} {rows:>9,} rows {secs:>5.1f}s -> "
                          f"{os.path.basename(paths[0]) if paths else '?'}")
        todo = [s for s in plan if s["id"] not in done]
        st["total_seconds"] = round(st["total_seconds"] + (time.time() - t_start), 1)
        save_state(st)
        rounds += 1
        t_start_round = time.time()

    print(f"invocation done: {rounds} round(s), {len(done)}/{len(plan)} shards complete")
    if not todo:
        print("ALL_SHARDS_COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
