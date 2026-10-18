WYVERN Wind Tunnel STL Package v2
Skylight Industries LLC
PDR-002 Rev B — Generated April 2026
═══════════════════════════════════════════════════════

TEST SECTION: 150×150 mm square bore
CONTRACTION:  9:1, Bell 5th-order polynomial
TOTAL LENGTH: ~2,470 mm assembled
FAN TARGET:   AC Infinity Cloudline T8 (200mm, ~250 CFM)
WALL THICKNESS: 3.0 mm throughout

ALL UNITS: millimetres
ALL MODELS: watertight binary STL, normals computed analytically

═══════════════════════════════════════════════════════
FILE INDEX
═══════════════════════════════════════════════════════

FLOW PATH (inlet → outlet):

01_bellmouth_inlet_120mm.stl
   Elliptic Eckert-profile inlet. Inner radius sweeps r=125→78mm over 120mm.
   64-segment circular cross-section, 16 axial stations. 3mm wall.
   Print orientation: inlet face down. No support required.

02_settling_chamber_150mm.stl
   156×156mm exterior square tube, 150×150mm bore, 150mm long.
   Print ×2. Provides turbulence decay length upstream of screens.
   32 tris — geometrically complete (4 outer walls + 4 inner walls + 8 end-cap quads).

03_honeycomb_frame_50mm.stl
   Same 156×156 profile, 50mm long.
   IN SLICER: set infill to Honeycomb/Grid at 3mm cell size, 0 top/bottom skins.
   This converts the volume into the flow-conditioning honeycomb insert.

04_screen_frame_40mm.stl
   Same profile, 40mm long, with inner ledge at z=18–22mm.
   PRINT PROCEDURE: Pause at layer 18mm, embed 150×150mm wire mesh (18 mesh/cm²),
   resume. The ledge retains the mesh. Print ×2.

05_smoke_strut_section_100mm.stl
   Same profile, 100mm long. Nine 4mm-dia boss protrusions (3×3 grid,
   ±50mm pitch) on Y- face for smoke/fog injection tubing.
   Boss protrusions are modelled — no slicer modification needed.

06A–06F_contraction_cone_seg*.stl
   Six 150mm segments composing the 900mm Bell 5th-order polynomial contraction.
   9:1 area ratio: 450×450mm bore inlet → 150×150mm bore outlet.
   Bell polynomial: f(ξ) = 6ξ⁵ − 15ξ⁴ + 10ξ³
   Outer wall tapers with bore (3mm constant wall thickness throughout).
   BORE PROFILE:
     Seg A (z=0–150mm):   bore half 225.0 → 219.7mm
     Seg B (z=150–300mm): bore half 219.7 → 193.5mm
     Seg C (z=300–450mm): bore half 193.5 → 150.0mm
     Seg D (z=450–600mm): bore half 150.0 → 106.5mm
     Seg E (z=600–750mm): bore half 106.5 →  80.3mm
     Seg F (z=750–900mm): bore half  80.3 →  75.0mm
   Each segment requires junction rings at both faces.
   IMPORTANT: Seg A–C require large junction rings (11). Seg D–F transition
   toward test section size — use small junction rings (12) at outlet.

07A_test_section_167mm.stl
07B_test_section_167mm.stl  [geometrically identical to 07A — same 167mm length]
07C_test_section_166mm.stl
   156×156mm exterior, 150×150mm bore. Three segments compose the 500mm test section.
   WINDOW SLOTS: In slicer, subtract four 130mm(W)×80mm(H) rectangular negative
   volumes, one per face, centred axially on each piece at mid-height.
   These become the acrylic window openings for flow visualization access.
   Acrylic glazing: 2mm laser-cut from 150×500mm polycarbonate sheet.

08_diffuser_sq_to_circle_220mm.stl
   Square-to-circle transition. Inlet: 150×150mm square. Outlet: R=100mm circle.
   4.0° half-angle (Barlow, Rae & Pope separation threshold).
   Corner radius grows linearly 0→100mm. 64-segment circular approximation.
   Mates to fan housing (09) at circular outlet.

09_fan_housing_200mm_dia.stl
   200mm OD circular duct housing, 60mm axial, 3mm wall.
   Four integral mounting lugs at 90° intervals for AC Infinity T8 flange bolts.
   Fan assembly (10) is inserted axially from outlet face.

10_fan_assembly_7blade.stl
   7-blade axial fan rotor. Hub: R=18mm solid disc, 55mm long.
   Blades: chord=28mm, span=77mm (hub R=18 to tip R=95mm).
   Root pitch = 32°, wash-out = 8° linear tip twist.
   Sweep = 20° forward. NACA simplified thickness distribution.
   PRINT: Use 4 walls, 40% gyroid infill for blade structural integrity.
   BALANCE: After printing, dynamically balance before installation.
   NOTE: This is a visualization model, not a high-performance rotor.
   Replace with AC Infinity OEM rotor for maximum airflow.

11_junction_ring_large_156sq_30mm.stl
   Compression coupling for settling chamber modules (156mm exterior).
   Inner socket lip: 5mm axial depth, 2mm radial thickness.
   Provides 2mm press-fit socket on each face for module alignment.

12_junction_ring_small_156sq_20mm.stl
   Compression coupling for test section modules (156mm exterior, tighter bore).
   Inner socket lip: 4mm axial depth, 1.5mm radial thickness.

13_sting_mount_aoa_bracket.stl
   Gridfinity-compatible base (84×84mm, 5mm thick).
   Integral octagonal sting post: 10mm across-flats, 120mm tall.
   AoA indexing arm: 30mm radial extension at post apex.
   BORE: 4mm axial hole through post for CF sting rod (user drills post-print).
   Compatible with TAL221 50g load cell in-line force balance per PDR-002 §6.

14_fin_module_clamp_half.stl
   Split C-clamp (print ×2) for body stub mounting of fin ring assemblies.
   Inner clamp bore: R=12mm (fits 23.3mm OD 1:3-scale body stub).
   Radial arm: 40mm extension for fin panel attachment.
   ASSEMBLY: Two halves + 2× M3×20 socket head cap screws.
   3mm bolt holes: user drills at flat faces post-print.

═══════════════════════════════════════════════════════
SLICER TASKS (cannot be generated without boolean backend)
═══════════════════════════════════════════════════════

1. Test section window slots (07A/B/C):
   Add four 130×80mm rectangular negative volumes per piece, centered
   on each face. Bambu Studio: Modifier mesh → Negative Volume.

2. Smoke strut port bores (05):
   Boss protrusions are modelled. User drills 4mm bore through each boss
   post-print, or add 4mm cylinder negative volumes in slicer before printing.

3. Sting post CF rod bore (13):
   Drill 4mm axial hole through sting post center, full depth.

4. Fin clamp M3 holes (14):
   Drill 3mm holes at clamp flat faces, ×2 per half, at z=5mm and z=10mm.

═══════════════════════════════════════════════════════
PRINT SETTINGS (PETG-CF recommended for all aerodynamic surfaces)
═══════════════════════════════════════════════════════

Aerodynamic surfaces (bellmouth, contraction, diffuser):
  Layer height: 0.15mm | Walls: 3 | Infill: 20% gyroid | Temp: 240°C

Structural modules (settling chamber, screen frame, test section):
  Layer height: 0.20mm | Walls: 4 | Infill: 25% gyroid

Fan assembly:
  Layer height: 0.15mm | Walls: 4 | Infill: 40% gyroid | Orient: blade tip up

Brackets and rings:
  Layer height: 0.20mm | Walls: 4 | Infill: 40% rectilinear

Surface finish: sand 220→400 grit, 2 coats Rust-Oleum 2X primer.
Equivalent sand-grain roughness target: <5μm.

═══════════════════════════════════════════════════════
REFERENCES
═══════════════════════════════════════════════════════
Barlow, Rae & Pope (1999) Low-Speed Wind Tunnel Testing, 3rd ed.
Hofferth (2025) Modular Wind Tunnel for STEM Education, AIAA SciTech.
Bell polynomial contraction profile: Fang & Elbaz (1984) J. Fluids Eng.
