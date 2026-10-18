---
source_file: "XRIM117_WYVERN_TechOverview.docx"
source_type: "DOCX"
updated_at: 2026-05-26
---
# XRIM117_WYVERN_TechOverview

*Extracted from [[XRIM117_WYVERN_TechOverview.docx]]*

---

**XRIM-117 WYVERN**

Technology Overview --- Companion Document

**Prototype Technology Demonstrator · PDR-002 Rev A**

Skylight Industries LLC

**CONFIDENTIAL --- FOR DISCUSSION PURPOSES ONLY --- NOT FOR DISTRIBUTION**

1\. Executive Summary

The XRIM-117 WYVERN Prototype Technology Demonstrator (PTD) is a 70mm-diameter autonomous guided rocket platform developed by Skylight Industries LLC to validate a hybrid flight-control architecture in a recoverable, repeatably-flyable subscale vehicle. The programme uses commercially available hobby rocketry hardware, custom-designed electronics, and PETG-CF printed structure throughout.

The vehicle integrates two independent rings of four aerodynamic control fins with a ceramic jetavane thrust-vector control system --- a novel approach at hobby scale that simultaneously provides attitude control and analogue thrust modulation from the same actuator. A three-board distributed avionics stack with redundant inertial measurement and independent power domains handles all flight-critical functions autonomously, with real-time datalink to a ground control station.

  --------------------------- --------------------------------------------------------------------------------
  **Programme designation**   XRIM-117 WYVERN PTD PDR-002 Rev A
  **Organisation**            Skylight Industries LLC
  **Vehicle class**           Subscale autonomous guided demonstrator --- hobby motor propulsion
  **Primary objective**       Validate hybrid aerodynamic + TVC control architecture in powered flight
  **Scale**                   1:2.14 geometric scale
  **Body diameter**           70mm OD / 68mm ID
  **Overall length**          \~1,170mm
  **All-up mass (est.)**      \~640g
  **Propulsion**              Two-stage commercial solid motors --- 29mm booster + 38mm sustainer
  **Launch mode**             1010 aluminium extrusion rail, near-vertical, 1.83m
  **Recovery**                Computer-triggered ejection charge --- nose cone separation --- 24in parachute
  **Datalink**                915MHz LoRa --- \~2km line-of-sight
  **Build cost (est.)**       \~\$660 USD per vehicle (one-time PCB setup included)
  --------------------------- --------------------------------------------------------------------------------

2\. Vehicle Architecture

2.1 Airframe
------------

The primary structure is a PETG-CF 20% carbon-fibre-reinforced printed outer shell laminated over a 70mm OD / 68mm ID phenolic tube liner that provides the structural backbone. All external aerodynamic and structural components --- fin cans, centering rings, nose cone, TVC frame, and avionics sled --- are printed in PETG-CF. The avionics sled and nose bay use PLA where thermal loading is not a concern.
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ------------------------- -------------------------------------------------------------------------
  **Body tube**             70mm OD / 68mm ID phenolic liner + PETG-CF 20% CF outer shell
  **Overall length**        \~1,170mm across three bolted sections
  **Forward section**       \~270mm --- nose cone bay + parachute bay
  **Mid section**           \~490mm --- CCM avionics sled + ASAM-1 + mid fin ring
  **Aft section**           \~410mm --- ASAM-2 + 38mm sustainer + jetavane + aft fin ring + booster
  **Nose cone profile**     Von Karman ogive (Haack LV series), 234mm, PETG-CF
  **Section coupling**      PETG-CF centering rings + M3 nylon-tipped set screws per joint
  **Print specification**   0.2mm layer height, 3--4 perimeter walls, 40--60% gyroid infill
  ------------------------- -------------------------------------------------------------------------

2.2 Aerodynamic Control Surfaces
--------------------------------

One active ring of four all-moving mid fins provides primary pitch, yaw, and roll authority. Ring 1 (aft stabilisers) is passive --- four fixed fins bonded into the aft fin can provide baseline aerodynamic stability without active control. Ring 2 (mid canard-style fins, clocked 45° to Ring 1) provides primary pitch, yaw, and roll authority at speed. The four Ring 2 fins are independently servo-actuated on a 7.4V high-voltage rail; Ring 1 is fixed (no servos).
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ------------------ --------------------------------------- ------------------------------------------
  **Parameter**      **Ring 1 --- Aft Stabilisers**          **Ring 2 --- Mid Control Fins**
  Quantity           4, at 90° spacing                       4, at 90° spacing, clocked 45° to Ring 1
  Root chord         93mm                                    47mm
  Tip chord          47mm                                    23mm
  Span               70mm                                    35mm
  Actuation          None --- fixed bonded root (no servo)   KST X08 Plus HV --- 1 servo per fin
  Max deflection     0° (fixed)                              ±25°
  Pivot axis         None --- epoxy-bonded into fin can      50% chord
  Servo controller   None --- no PWM channels required       ASAM-1 (TIM1\_CH1--4)
  ------------------ --------------------------------------- ------------------------------------------

 

3\. Propulsion System

3.1 Two-Stage Architecture
--------------------------

Stage 1 (29mm booster) accelerates the vehicle off the rail. At burnout, a spring-loaded ejection ring separates the booster casing rearward --- the casing deploys a streamer and descends separately. Stage 2 (38mm sustainer) provides thrust for altitude hold, loiter, and the landing burn, operating through the ceramic jetavane TVC system.
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  --------------------- --------------------------------------- ----------------------------------------
  **Parameter**         **Stage 1 --- Booster (29mm)**          **Stage 2 --- Sustainer (38mm)**
  Motor class           F impulse --- commercial hobby reload   G impulse --- commercial hobby reload
  Candidate (nominal)   Cesaroni F39-6T                         AeroTech G76-10G (\~10s burn, avg 76N)
  Total impulse         80--120 N·s                             \~637 N·s (G76)
  TVC                   None --- fixed mount                    Ceramic jetavane [±]{dir="rtl"}45°
  Retention             Eject-design --- no aft retainer        Aeropack 38mm threaded retainer
  Recovery              Streamer via ejection charge            Sustainer section --- main parachute
  --------------------- --------------------------------------- ----------------------------------------

3.2 Ceramic Jetavane TVC System
-------------------------------

The sustainer TVC system uses two ceramic jetavanes --- one per axis (pitch, yaw) --- mounted inside the nozzle diverging section on titanium pivot shafts. Each vane is independently servo-driven by ASAM-2 and rotates up to [±]{dir="rtl"}45° from the flow axis. This simultaneously deflects the exhaust vector for attitude control and partially occludes the nozzle exit area to reduce effective thrust --- providing analogue throttle authority over the otherwise fixed-thrust motor. The motor mount is fixed; no outer gimbal ring is required.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

⚠ *Jetavane TVC is the operating principle used in the V-2 (1942) and numerous early surface-to-air missile systems. Graphite vanes were standard in those applications; WYVERN uses Macor machinable glass-ceramic, which handles 1000°C continuous service temperature --- adequate for hobby solid motor burn durations under 10 seconds.*
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ------------------------- ----------------------------------------------------------------------------------------
  **Vane material**         Macor machinable glass-ceramic (prototyping) / ZTA zirconia-toughened alumina (flight)
  **Max service temp**      Macor: 1000°C · ZTA: 1500°C · Nozzle diverging-section wall: \~800--1200°C
  **Vane geometry**         \~12mm wide × 22mm tall × 3mm thick rectangular plate
  **Pivot shaft**           3mm titanium rod through nozzle wall, sealed with high-temp RTV
  **Actuators (×2)**        KST X08 Plus HV · TIM2\_CH1 (pitch) · TIM2\_CH2 (yaw) on ASAM-2 7.4V HV rail
  **Deflection range**      [±]{dir="rtl"}45° vane rotation · \~20° effective exhaust deflection at max angle
  **Thrust modulation**     0° → \~100% rated thrust [· ±]{dir="rtl"}45° → \~35% rated thrust
  **Fail-safe**             Spring return to 0° on servo power loss --- full thrust, neutral vector
  **Impulse loss (est.)**   \~3--5% of total impulse due to vane drag --- acceptable for demonstrator
  ------------------------- ----------------------------------------------------------------------------------------

 

4\. Avionics Architecture

4.1 Three-Board Distributed Stack
---------------------------------

The avionics architecture distributes flight-critical functions across three 62mm circular custom PCBs, each with its own LiPo power source and redundant sensor suite. This eliminates single-board failure as a mission-ending event and allows parallel testing of each module independently.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ----------- ----------- ------------------------------------------------------------- ------------------- -------------
  **Board**   **MCU**     **Primary function**                                          **Servo outputs**   **Battery**
  CCM         RP2040      Guidance, LoRa datalink, 3× pyro MOSFET                       None                1S 850mAh
  ASAM-1      STM32F411   Mid ring fins, redundant IMU+baro                             4× Ring 2 fins      1S 1000mAh
  ASAM-2      STM32F411   Jetavane TVC, sustainer relay (Ring 1 aft fins are passive)   2× jetavane         1S 1200mAh
  ----------- ----------- ------------------------------------------------------------- ------------------- -------------

4.2 Central Command Module (CCM)
--------------------------------

The CCM is the guidance law executor and datalink hub. It runs the full 8-phase state machine, fuses inertial and barometric data from all three boards, commands fin and jetavane deflections to the ASAMs over UART, and fires pyrotechnic channels for staging and recovery.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ------------------- --------------------------------------------------------------------------------------
  **MCU**             RP2040 --- dual Cortex-M0+ @ 133MHz, 264KB SRAM, 16MB QSPI flash (telemetry log)
  **IMU**             ICM-42688-P --- SPI, 32kHz ODR (primary inertial reference)
  **Barometer**       BMP388 --- I2C, 200Hz (primary altitude reference)
  **Datalink**        Ebyte E22-900M22S --- SX1268, 915MHz ISM, 22dBm EIRP --- 915MHz quarter-wave antenna
  **Pyro channels**   3× IRFZ44N MOSFET --- CH1 nose chute · CH2 sustainer ignition relay · CH3 spare
  **Inter-board**     UART 115200 baud (commands) · SPI 4MHz (IMU data) · I2C 400kHz (baro) · JST-GH 8-pin
  **Arming**          Physical switch + software arm --- hardware interlock prevents accidental pyro fire
  ------------------- --------------------------------------------------------------------------------------

4.3 Auxiliary Sensor & Actuator Modules (ASAM-1 / ASAM-2)
---------------------------------------------------------

Both ASAM boards share the same MCU (STM32F411 Cortex-M4 at 100MHz with FPU), sensor suite (ICM-42688-P + MS5611), and 7.4V HV servo rail (MT3608 boost converter from 1S LiPo). ASAM-2 additionally hosts the sustainer ignition relay (IRFZ44N + PC817 optocoupler isolation) and drives two additional jetavane servo channels.
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  ----------------------- ---------------------------------------------------------------------------------------------
  **MCU (both)**          STM32F411CEU6 --- Cortex-M4 @ 100MHz, FPU, 512KB flash, 128KB SRAM
  **Sensors (both)**      ICM-42688-P (SPI 32kHz) + MS5611 barometer (SPI 150Hz) --- redundant to CCM
  **Servo rail**          MT3608 boost converter: 1S LiPo → 7.4V HV --- all servos run at high voltage for max torque
  **Servo spec**          KST X08 Plus HV --- 8g, ≥3.85 kg·cm @ 6V, 5.3 kg·cm @ 8.4V, 0.09s/60°
  **PWM generation**      STM32 hardware timers --- 50Hz frame, 1000--2000μs --- TIM1 fins, TIM2 jetavane/relay
  **Board form factor**   62mm circular, 2-layer FR4, ENIG finish --- fits 68mm ID tube with 3mm clearance
  **Fabrication**         JLCPCB --- bare boards + SMT assembly for MCUs, IMUs, barometers, passives
  ----------------------- ---------------------------------------------------------------------------------------------

4.4 915MHz Datalink
-------------------

The CCM hosts an Ebyte E22-900M22S LoRa module (SX1268 chipset) providing two-way communication at 915MHz ISM band. A 77mm quarter-wave monopole antenna exits through the tube wall sealed with silicone RTV. The ground control station runs custom Python software on a Raspberry Pi 4 with a matching E22 USB dongle.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  --------------------- --------------------------------------------------------------------------------------------
  **Downlink (10Hz)**   Altitude · velocity · attitude quaternion · fin positions · battery voltages · motor state
  **Uplink**            Target altitude command · abort flag · arm-landing command · CRC16 validated frame
  **Range**             \~2km line-of-sight at SF9, 125kHz bandwidth --- adequate for all planned flight envelopes
  **GCS hardware**      Raspberry Pi 4 · Ebyte E22 USB dongle · 7in touchscreen · Python GCS · SQLite log
  --------------------- --------------------------------------------------------------------------------------------

 

5\. Autonomous Flight Profile

5.1 State Machine
-----------------

The CCM executes an 8-phase deterministic state machine. All phase transitions are triggered by sensor events or uplinked commands --- there is no time-based sequencing except the sustainer ignition delay.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  -------- ------------------ -------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  **\#**   **Phase**          **Duration**   **Trigger & action**
  0        Safe               Pre-arm        Physical arm switch OFF. All pyro disabled. Servos neutral.
  1        Armed              T-30s→T0       Switch ON. IMU/baro calibration. GCS link verified. Pyro continuity confirmed. Target altitude uplinked.
  2        Boost              \~0--2.5s      Launch command fires booster igniter. Vehicle accelerates off rail. Fins neutral (insufficient airspeed authority).
  3        Rail clear         \~2.5--5s      Rail clearance detected. Fin control loops activate. Attitude hold --- vertical --- via differential fin deflection.
  4        Staging            \~5--7s        Booster burnout + delay fires ejection ring. Casing separates + streamer deploys. CCM fires sustainer igniter at eject+0.2s.
  5        Sustainer loiter   \~7--17s       Sustainer burns. TVC jetavane + all 4 Ring 2 mid fins active (Ring 1 aft fins are passive). CCM altitude hold: targets uplinked AGL (90--150m). Loiter 10--20s.
  6        Powered descent    \~17--24s      CCM initiates landing burn. Jetavane modulates thrust for controlled deceleration. \<1 m/s target at touchdown.
  7        Touchdown          T+24s          Accelerometer spike \>10g axial. CCM logs event. All pyro disarmed. Servos neutral.
  8        Abort              Any phase      GCS abort command OR attitude error \>45° for \>0.5s OR altitude runaway → ejection charge fires → 24in chute deploys.
  -------- ------------------ -------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------

5.2 Guidance & Control Laws
---------------------------

  ---------------------- --------------------------------------------------------------------------------------------------------------------------
  **Architecture**       Cascaded PID --- outer loop: altitude error → pitch/yaw setpoint; inner loop: attitude error → fin + jetavane commands
  **Fin mixing**         Pitch: [±]{dir="rtl"}symmetric top/bottom fins · Yaw: [±]{dir="rtl"}symmetric left/right fins · Roll: differential all-4
  **Jetavane mixing**    Pitch: vane A · Yaw: vane B --- decoupled command matrix from CCM
  **Update rate**        500Hz ASAM MCUs (servo PWM at 50Hz, interpolated) · 100Hz CCM state machine
  **IMU fusion**         Mahony AHRS on each ASAM · CCM averages three quaternion estimates · outlier rejection at \>3° discrepancy
  **Altitude filter**    Complementary filter combining barometer altitude (CCM) and IMU vertical acceleration
  **Landing guidance**   Fixed thrust profile --- jetavane vane angle mapped to target thrust% for deceleration from \~5m/s to \<1m/s
  ---------------------- --------------------------------------------------------------------------------------------------------------------------

 

6\. Programme Budget

All components are sourced from commercial hobby rocketry and COTS electronics suppliers. No custom tooling, proprietary components, or controlled materials are required. The programme is designed to be repeatable: after initial PCB setup cost, subsequent builds reduce to approximately \$280 per vehicle.

  ------------------------------------------------------------------ ------------------------ --------- ---------- -------------
  **Item**                                                           **Source**               **Qty**   **Unit**   **Total**
  70mm OD phenolic/fiberglass body tube (1.2m)                       Apogee / LOC             1         \$22       \$22
  PETG-CF filament 20% CF (750g)                                     eSUN / Polymaker         1         \$32       \$32
  KST X08 Plus HV micro-servo (×6 --- 4 mid fins + 2 jetavane TVC)   HobbyKing                6         \$13       \$78
  AeroTech G76-10G 38mm sustainer motor                              Local club               2         \$38       \$76
  Cesaroni F39-6T 29mm booster motor                                 Local club               2         \$24       \$48
  Macor ceramic rod 12mm dia ×50mm                                   McMaster-Carr            1         \$24       \$24
  PCB fabrication --- 3 designs (CCM, ASAM-1, ASAM-2), 5pcs ea.      JLCPCB                   1 set     \$27       \$27
  SMT assembly --- CCM, ASAM-1, ASAM-2 (MCUs + sensors + passives)   JLCPCB                   1 set     \$110      \$110
  Electronic components (IMUs, LoRa, MOSFETs, converters, LiPos)     LCSC / AliExpress        1 set     \$78       \$78
  24in parachute + Kevlar harness                                    Apogee / Fruity Chutes   1         \$39       \$39
  1010 aluminium rail 6ft + launch hardware                          Misumi / 80/20           1         \$22       \$22
  CF pushrods, Ti hardware, black powder, epoxy, misc.               Various                  1         \$52       \$52
  **TOTAL ESTIMATED BUILD COST**                                                                                   **\~\$660**
  ------------------------------------------------------------------ ------------------------ --------- ---------- -------------

⚠ *Motors (\$124) are the largest recurring cost per flight campaign. PCB fabrication and SMT assembly (\$137) are one-time setup costs --- the 5-pack minimum from JLCPCB yields 4 spare boards per design. Subsequent vehicle builds reduce to approximately \$280--300 total.*

7\. Safety & Regulatory Compliance

The XRIM-117 WYVERN PTD is a research and development platform operated under hobby rocketry frameworks. All propulsion uses commercially available, BATFE-exempt certified hobby rocket motors. No classified, ITAR-controlled, or export-restricted components or technical data are used or referenced in this programme.

7.1 Regulatory Framework
------------------------

NAR (National Association of Rocketry) safety code compliance for all flight operations

FAA notification required for flights above 400ft AGL --- TFR waiver filed per local club procedure

All motors are commercially certified hobby reloads --- no BATFE licensing required at F/G impulse class

Recovery zone: minimum 75m radius cleared downrange of prevailing wind

Two independent recovery systems: primary (computer-triggered chute) + passive booster streamer

7.2 Arming & Safety Interlock
-----------------------------

Physical arming switch provides hardware interlock --- pyrotechnic channels cannot fire when disarmed

Software arm required in addition to physical switch --- dual-condition gate prevents accidental ignition

GCS abort command triggers immediate parachute deployment from any flight phase

Automatic abort on attitude error \>45° for \>0.5s --- covers loss of control, structural failure, TVC failure

Fail-safe on datalink loss: vehicle completes current phase autonomously --- no datalink dependency for safety

7.3 Export Control Statement
----------------------------

This document contains NO technical data subject to ITAR (International Traffic in Arms Regulations) or EAR (Export Administration Regulations) controls. All vehicle designs, avionics architectures, and control system descriptions are based entirely on publicly available hobby rocketry, open-source electronics, and non-controlled commercial components. This document may be shared with domestic persons without export licence. Recipients are advised to conduct their own compliance review before any international distribution.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

 

8\. Build & Test Programme

The programme runs across five sequential phases from design through flight test. Total duration from design kickoff to first full-profile flight is approximately 12--14 weeks, depending on PCB lead times and field access.

  ------------------------------------------------------ ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Phase 1 --- Design & Fabrication (Wks 1--3)**        OpenRocket model + stability verification. PETG-CF parts CAD. PCB design in EasyEDA (62mm circular). Order PCBs from JLCPCB with SMT assembly. Order motors, hardware, Macor rod.
  **Phase 2 --- Print & Mechanical (Wks 3--5)**          Print all PETG-CF structural parts. Assemble fin cans, TVC frame, centering rings. Machine Macor jetavane vanes on mini-lathe. Bond to Ti pivot shafts with Resbond 907. Test booster ejection ring.
  **Phase 3 --- Electronics (Wks 5--7)**                 Receive JLCPCB boards. Hand-solder through-hole connectors and MOSFET. Flash firmware. Calibrate all IMUs and barometers. Full 6-servo bench sweep (4 mid fins + 2 jetavane TVC). Test pyro channels. Verify GCS datalink.
  **Phase 4 --- Integration & Ground Test (Wks 7--8)**   Install avionics sled. Route wiring and antenna. Ejection charge ground test (0.45g BP). Jetavane static-flow test. Full pre-flight systems check with GCS.
  **Phase 5 --- Flight Test Campaign (Wk 9+)**           Flight 1: booster only --- rail clearance, stability, chute recovery. Flight 2: two-stage, chute recovery --- staging, sustainer ignition, altitude hold. Flight 3+: full profile --- progressive altitude increase, PID refinement, landing accuracy logging.
  ------------------------------------------------------ ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
