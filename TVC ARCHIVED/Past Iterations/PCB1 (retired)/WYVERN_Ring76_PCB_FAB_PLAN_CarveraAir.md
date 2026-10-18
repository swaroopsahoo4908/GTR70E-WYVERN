# PCB Fabrication Plan, Carvera Air (Isolation Routing)

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


General process for milling copper-clad boards on the Carvera Air with the PCB kit, using the `skylight-cam-toolpaths` skill's `gcode_toolpaths.py` library. This is the repeatable workflow, not tied to a specific board, use the DFM ceiling in §1 to decide *which* boards from this repo are actually candidates before running the rest of the process.

## 1. Design-for-manufacture ceiling, check this before starting

Isolation routing cuts a channel around each trace with a V-bit rather than etching the copper away entirely. Channel width at the surface is a function of bit angle and plunge depth:

$$w = 2 \cdot d \cdot \tan(\theta/2)$$

where $d$ is plunge depth and $\theta$ is the V-bit's included angle. For a typical 30° bit at 0.1mm depth, $w \approx 0.054$mm of pure channel, in practice, real starting points land 0.15-0.25mm once air-gap margin is added on both sides of the cut. That's workable for 0.5mm-pitch parts and coarser. It is *not* enough for 0.4mm-pitch or finer QFN/LFCSP breakout routing without going deeper than is good for the bit or the FR4 weave underneath.

Rule of thumb before committing a board to this process: pull the finest pin pitch on the board. 0.5mm and up, isolation routing is a reasonable bet. 0.4mm or finer, send it to JLCPCB instead, this machine isn't the right tool for that density, full stop. Ring76's audit trail this session confirmed U1 (RP2350B), U3 (BQ25798), and U18 (ADAU1450) are all 0.4mm pitch, which is why the full flight board stays on professional fab; the ejection-driver sub-circuit (U12 MCP23008 SOIC-18, Q1/Q2 SOT-23-3, D1/D2 SOD-123, all 0402 passives) has nothing finer than 1.27mm pitch and is a genuinely good candidate if a standalone bench-test version is ever wanted.

## 2. Front end, getting from schematic to millable geometry

1. Export Gerbers from EasyEDA Pro for the board in question (copper layer(s), drill file, board outline).
2. Run Makera's own Gerber-to-DXF converter (referenced in their FAQ) to turn the copper layer into 2D vector polylines. This skill does not parse Gerber or KiCad output directly, the conversion happens here, outside the CAM step.
3. The result is ordered (x, y) point lists in mm for each trace polygon, plus a drill-hit list and an outline polygon. This is the geometry `gcode_toolpaths.py` actually consumes.
4. Before generating toolpaths, offset the trace polylines inward from their true copper edge by half the computed channel width plus your desired air gap, `emit_pcb_isolation()` does not compute this offset itself; it has to be done on the geometry going in.

## 3. Operation order, always isolate, then drill, then cut out

This order matters and shouldn't be shuffled without a specific reason:

1. *Isolation routing* first, while the board is still fully backed by surrounding stock, the most precision-sensitive pass, wants maximum rigidity.
2. *Drilling* second, component leads and vias at 0.6-1.0mm carbide, single pass on standard 1.6mm FR4 (no pecking needed at that thickness). Mounting holes sized to the actual hardware (typically 2.5-3.2mm for M2.5/M3).
3. *Outline cutout* last, with tabs, freeing the board before the earlier passes finish is how you get a part that shifts mid-job and ruins both remaining operations.

Drill-before-isolation is also valid if you want hole positions as an alignment check against a printed or projected reference on a dense board; either order is electrically fine, it's a workholding/alignment tradeoff, not a correctness one.

## 4. Tooling and feeds/speeds

| Operation | Tool | RPM | Feed | Depth |
|---|---|---|---|---|
| Isolation routing | V-bit, 10-30° included angle | 10,000-13,000 | 300-500mm/min | 0.1-0.15mm |
| Drilling (leads/vias) | 0.6-1.0mm carbide drill | 12,000-13,000 | 150-250mm/min | full thickness, 1 pass |
| Mounting holes | Sized to hardware (2.5-3.2mm) | 12,000-13,000 | 150-250mm/min | full thickness, 1 pass |
| Outline cutout | 0.8-1.0mm end mill | per material table | reduced ~20% from roughing feed | 2-3 shallow passes, not one deep pass |

Deeper isolation cuts only if continuity testing turns up bridged traces afterward, going deeper than needed wears carbide fast and risks nicking the fiberglass weave, which is harder on a bit than the copper itself. Always dwell 1.5-3 seconds after `M3 S<rpm>` before the first cutting move; the closed-loop spindle needs a moment to reach commanded RPM. Wear a respirator or run supplemented dust collection, FR4 dust is glass fiber plus resin, a real respiratory irritant beyond what wood dust is.

## 5. Generating the actual toolpath file

Once geometry is in hand, this is a direct call into the skill's library, worth re-invoking `skylight-cam-toolpaths` at that point rather than hand-rolling G-code:

1. `emit_pcb_isolation()` on the offset trace polygons.
2. `emit_pcb_drill()` on the hole list.
3. `emit_pcb_outline()` on the board boundary, tabs on by default (three, 2mm wide, evenly spaced, don't turn these off; an untabbed board that comes free mid-cut can catch the bit).
4. `assemble_job()` wraps all three into one file with correct header/footer and safe-Z moves between operations.
5. Run the paired `plot_toolpath.py` preview before anything touches the machine, cheap insurance against a geometry mistake that isolation-routes the wrong side of a trace.
6. Export to `/mnt/user-data/outputs/`, load into Carvera Controller, and always air-cut or trace-only a first pass on scrap copper-clad before committing the real blank.

## 6. Post-mill QA, before any component goes on

1. Continuity check every net with a multimeter against the source netlist, the .tel file's $NETS section is still the ground truth here, same as it's been for every wiring pass this session. This is the step that catches an isolation channel that didn't fully clear (bridged trace) or clipped a trace it shouldn't have (open where continuity is expected).
2. Visual/loupe or microscope check around any denser breakout areas even after continuity passes clean, a channel that's marginal but not yet bridged today can flex/oxidize into a bridge later.
3. Snap tabs by hand, deburr the board edge, then proceed to assembly.

## 7. When to use this machine vs. JLCPCB

Carvera Air + isolation routing: single/double-sided boards, coarsest pitch on the board 0.5mm or larger, low net-count boards, same-day turnaround wanted, or a bench-test/breakout board that doesn't need to fly. Manual through-hole vias only, no real multilayer or blind-via capability here.

JLCPCB (or equivalent professional fab): anything with 0.4mm pitch or finer present (Ring76's flight board, categorically, per §1), anything needing more than 2 layers, anything where trace/space needs to be tighter than what a V-bit channel can hold, or anything that's actually flying and needs the reliability margin professional fab + soldermask + real plating gives you over a hand-milled board.
