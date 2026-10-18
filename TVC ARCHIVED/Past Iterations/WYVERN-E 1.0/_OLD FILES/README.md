# _OLD FILES — archived, superseded material

Moved out of `WYVERN-E 2.0/` on 2026-06-18. Nothing here is needed for the current
(two-board) iteration; kept only for reference/history. Original folder structure is
preserved, so any item can be moved straight back to where it came from.

## What's here

*Superseded single-board PCB design* (`WYVERN_E2_FCM.*`) — the original one-board flight
computer, replaced by the two-board split (`WYVERN_E2_B1` + `WYVERN_E2_B2`):
- `PCB/FCM_KiCAD/WYVERN_E2_FCM.kicad_pcb/.sch/.pro/.prl`, `_placement.png`
- `PCB/FCM_KiCAD/gerbers/WYVERN_E2_FCM*` (gerbers, BOM, CPL, zip)
- `PCB/WYVERN_E2_FCM_PCB_Documentation.md`, `PCB/WYVERN_E2_FCM_HANDOFF_BRIEF.md`

*Build cruft / checkpoints / backups*:
- `*_route.pkl`, `route_state.pkl` (autorouter checkpoints), `DRC.rpt`
- `gen_fcm.py.bak`, `gen_fcm.py.bak2`
- `.history/` (editor local-history git), temp files, `__pycache__/`, `.DS_Store`

## Note
`gen_fcm.py` itself was NOT archived — it is still imported by the current build
(`project_file` and helpers), so it remains in `PCB/generator/`.
