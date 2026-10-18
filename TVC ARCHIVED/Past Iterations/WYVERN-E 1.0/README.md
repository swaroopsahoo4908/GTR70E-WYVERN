# WYVERN-E 1.0

An experimental 70/127 mm research rocket demonstrating jet-vane thrust-vector control and a
custom avionics stack, serving as the first hardware PDR for the XRIM-117 WYVERN concept.

A Skylight Rocketry venture. Architecture revision PDR-004. *Superseded by WYVERN-E 2.0
(open-source solenoid TVC + custom RP2350B two-board PCB).*

---

## Overview

WYVERN-E 1.0 established the physical design envelope — two body diameter candidates (70 mm PDR-002
and 127 mm PDR-003/004), a jet-vane TVC geometry, the wind tunnel test infrastructure, and the
first KiCad avionics layout (XRIM117 RevB/C and XRIM117E). The program reached PDR-004 full
assembly before being superseded by the cleaner open-source two-board architecture of 2.0.

---

## Folder structure

```
WYVERN-E 1.0/
├── README.md                          ← this file
├── CAD:Models:PCB/                    ← OpenRocket sims, STL parts, KiCad PCBs, SVG schematics
│   ├── XRIM117_PTD_PDR002_70mm.ork    ← 70 mm PDR-002 baseline sim
│   ├── XRIM117E_PDR003_127mm.ork      ← 127 mm PDR-003 sim
│   ├── XRIM117E_PDR003_127mm_F15.ork  ← 127 mm F15-motor variant
│   ├── XRIM117E_PDR003_127mm_FLIGHT.ork
│   ├── XRIM117E_PDR004_FULL.ork       ← PDR-004 full assembly sim
│   ├── XRIM117E_PDR004_TVC_ONLY.ork   ← PDR-004 TVC-only stage sim
│   ├── XRIM117_all_parts/             ← 19-part STL library (nose, tubes, fins, gimbal, motor mount…)
│   ├── XRIM117E_KiCAD_RevC/           ← XRIM117E avionics KiCad RevC
│   ├── XRIM117_KiCAD_RevB/            ← XRIM117 avionics KiCad RevB
│   ├── XRIM117_EasyEDA_v3/            ← EasyEDA schematic source (pre-KiCad migration)
│   ├── xrim117_avionics_v4.svg        ← avionics schematic (SVG)
│   ├── xrim117_jetavane_tvc.svg       ← jet-vane TVC diagram (SVG)
│   ├── XRIM117_PCB_Layouts.html       ← rendered PCB layout view
│   ├── WYVERN_Engineering_Analysis.pdf ← structural and aero analysis
│   └── WYVERN_Simulator.md            ← flight simulation environment notes
├── Wind Tunnel/                       ← wind tunnel design, BOM, and test data
│   ├── Wind Tunnel Build.md           ← construction and instrumentation notes
│   ├── wind_tunnel_bom.xlsx           ← wind tunnel bill of materials
│   ├── WYVERN_wind_tunnel_spec.html   ← tunnel specification (HTML)
│   ├── WindTunnel_all_parts/          ← 14-part STL assembly (bellmouth, settling chamber,
│   │                                     contraction cone ×6, test section ×3, diffuser, fan)
│   └── WYVERN_WindTunnel_v2.zip       ← full tunnel archive
├── Docs:Decks/                        ← presentations and technical overview documents
│   ├── XRIM117_WYVERN_PitchDeck.pptx ← investor/competition pitch deck
│   ├── XRIM117_WYVERN_TechOverview.docx ← technical overview document
│   ├── XRIM117_PTD_PDR002_RevA_70mm.docx ← PDR-002 preliminary design review
│   └── XRIM117_NDA.docx               ← NDA (superseded by WYVERN/WYVERN NDA.md)
└── _OLD FILES/                        ← superseded PCB revisions (kept for reference)
    └── PCB/FCM_KiCAD/                 ← earlier KiCad layout with gerbers
```

---

## Key design parameters (PDR-004)

| Parameter | Value |
|---|---|
| Body diameters evaluated | 70 mm (PDR-002), 127 mm (PDR-003/004) |
| TVC method | Jet-vane (carbon-composite vanes in motor exhaust) |
| Avionics | Custom KiCad PCB — XRIM117 RevB → XRIM117E RevC |
| Wind tunnel | Open-return, 14-part 3D-printed, bellmouth inlet |
| Simulation | OpenRocket + custom Python flight simulator |

---

## Related

- `../WYVERN-E 2.0/` — successor: open-source solenoid TVC + RP2350B two-board PCB
- `../WYVERN/` — XRIM-117 concept and doctrine documents
- [[WYVERN MOC]] — Obsidian index
