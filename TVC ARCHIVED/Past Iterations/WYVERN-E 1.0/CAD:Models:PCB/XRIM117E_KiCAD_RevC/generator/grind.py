#!/usr/bin/env python3
"""
PathFinder-lite rip-up-and-reroute driver — the capability a greedy A* lacks.

Strategy (negotiated-congestion, simplified):
  pass 0: route all nets in the given order.
  pass k: nets that failed last pass move to the FRONT (they pick routes first
          when the board is emptiest); everything re-routes from a clean board.
  keep the best (fewest-fail) result; stop when 0 fails or no improvement.

A "clean board each pass" = full rip-up. Failed-first ordering = congestion
negotiation: the hard nets claim the scarce channels before the easy ones fill them.
"""
import time, copy

def grind(build_fn, base_order, widths, name, time_budget=40.0, max_passes=14,
          retry_shrink=0.55):
    """build_fn() -> (board, netlist, route_one) where route_one(rt,net,width)->bool
       Actually we re-import per pass via build_fn returning a fresh (brd, sch_netlist,
       make_router) so each pass starts from clean copper."""
    from autoroute import Router, stitch_gnd
    t0=time.time()
    order=list(base_order)
    best=None  # (nfail, brd, fails)
    seen_fail_sets=set()
    for p in range(max_passes):
        if time.time()-t0>time_budget: break
        brd, netlist, allnets = build_fn()
        rt=Router(brd, widths)
        seq=[n for n in order if n in allnets]+sorted(allnets-set(order))
        fails=[]
        for net in seq:
            if time.time()-t0>time_budget:
                fails += [n for n in seq if n not in seq[:seq.index(net)]]
                break
            if not rt.route_one(net, widths.get(net,0.2)):
                # one shrink retry inline
                if not rt.route_one(net, max(0.2, widths.get(net,0.2)*retry_shrink)):
                    fails.append(net)
        nf=len(fails)
        if best is None or nf<best[0]:
            best=(nf, brd, netlist, list(fails))
        print(f"  pass {p}: {nf} fails  ({', '.join(fails[:8])}{'...' if nf>8 else ''})", flush=True)
        if nf==0: break
        fs=tuple(sorted(fails))
        if fs in seen_fail_sets:  # cycle — perturb order
            order = fails + [n for n in order if n not in fails][::-1]
        else:
            order = fails + [n for n in order if n not in fails]
        seen_fail_sets.add(fs)
    nf, brd, netlist, fails = best
    stitch_gnd(brd, spacing=7.0)
    brd.gnd_zone("F.Cu"); brd.gnd_zone("B.Cu")
    return brd, netlist, fails
