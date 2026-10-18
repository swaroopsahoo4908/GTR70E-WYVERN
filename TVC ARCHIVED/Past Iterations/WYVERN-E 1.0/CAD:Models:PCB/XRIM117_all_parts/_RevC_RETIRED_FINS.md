# PDR-003 Rev C — CAD Manifest Update (Finless Sustainer)

RETIRED by Rev C (do not print for the 127mm vehicle):
- 06_fin_ring1_aft.stl, 07_fin_ring2_mid.stl  (sustainer fin rings — sustainer is finless, solenoid TVC)
- 15_tvc_outer_ring.stl, 16_tvc_inner_cradle.stl (70mm servo-TVC rings — superseded by LSRG-S25 solenoid cradle)
- 18_pcb_asam1.stl, 19_pcb_asam2.stl (boards retired; see SDM 100mm)

STILL VALID for the booster only (scale fins per XRIM117E_PDR003_127mm.ork: root 185mm, tip 92mm, span 132mm, sweep 62mm, 5mm airfoil, 4x).

NEW Rev C parts:
- ../XRIM117E_camera_pod_fairing.stl — OV7670 side pod (34x30mm wedge, 11mm lens bore), mounts at +X azimuth, 120mm below sustainer tube top; lens port through airframe 11mm; pod faces J11 on the CCM.
- ../XRIM117E_PDR003_127mm.ork — two-stage 127mm: finless TVC sustainer + 4-fin booster.

Booster stability: enlarged fins move the booster-phase CP well aft; verify static margin 1.5-2.0 cal in OpenRocket with your chosen motors (sims must be re-run after motor selection — the solenoid stage adds 446g aft of the sustainer CG, the camera pod 22g lateral).

Rev C3 (F15 propulsion) additions:
- ../XRIM117E_PDR003_127mm_F15.ork — flight config: booster 3x Estes F15-0 (29mm cluster, 3-ring), sustainer 1x Estes F15-8
- ../XRIM117E_booster_cluster_ring_3x29mm.stl — print 2x (fwd + aft booster rings); bores 29.2mm, cluster radius 33mm
- 09_motor_tube_29mm.stl remains valid: print 4x total (3 booster cluster + 1 sustainer gimbal tube)
- 08_motor_tube_38mm.stl RETIRED (no 38mm motors in Rev C3)
- Class 1 mass ceiling 1500g liftoff: weigh before every flight.
