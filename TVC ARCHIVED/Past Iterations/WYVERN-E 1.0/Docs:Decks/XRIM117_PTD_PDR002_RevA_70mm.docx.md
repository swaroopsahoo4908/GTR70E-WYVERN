---
source_file: "XRIM117_PTD_PDR002_RevA_70mm.docx"
source_type: "DOCX"
updated_at: 2026-05-26
---
# XRIM117_PTD_PDR002_RevA_70mm

*Extracted from [[XRIM117_PTD_PDR002_RevA_70mm.docx]]*

---

**XRIM-117 WYVERN**

EXTENDED CALIBER PROTOTYPE TECHNOLOGY DEMONSTRATOR

**PDR-002 \| Revision A**

*70mm Rail-Launch Guided Demonstrator*

TVC + Active Mid Fins + Passive Aft Stabilizers + 3-PCB Distributed Avionics + 915MHz Datalink

**Skylight Industries LLC**

**CONFIDENTIAL --- PROPRIETARY --- NOT FOR DISTRIBUTION**

1\. Overview & Design Philosophy

The XRIM-117 WYVERN Extended Caliber Prototype Technology Demonstrator (PDR-002 Rev A) is a 70mm-diameter, rail-launch experimental rocket developed by Skylight Industries LLC to validate the core aeromechanical and guidance architecture of the full-scale XRIM-117 WYVERN interceptor at a scale larger and more capable than the 56mm PDR-001 platform.

The vehicle is designed exclusively for 1010/80-20 aluminum extrusion rail launch in near-vertical orientation. Rail launch provides controlled guidance through the low-speed boost phase and eliminates the complexity of pod integration, keeping the initial development program focused on the avionics, TVC, and active fin control objectives.

In lieu of a warhead section the demonstrator carries a parachute recovery bay in the forward fuselage. The flight profile demonstrates: rail launch, boost, controlled ascent to target altitude, loiter on a sustainer motor, and a powered vertical-descent landing --- guided by TVC and an active mid fin ring, with a passive aft stabilizer ring providing baseline aerodynamic stability.

1.1 Key Demonstrator Specifications
-----------------------------------

  ---------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------
  **Designation**              XRIM-117 PTD PDR-002 Rev A
  **Organization**             Skylight Industries LLC
  **Scale Factor**             1:2.14 from 150mm full-scale (70mm OD body tube)
  **Body Tube**                70mm OD / 68mm ID phenolic or fiberglass, Cesseroni-compatible diameter
  **OAL**                      \~1,170mm
  **Fin Configuration**        2× rings of 4 fins (Ring 2 all-moving, Ring 1 fixed) --- Ring 2 mid active fins (4, all-moving) + Ring 1 aft passive stabilizers (4, fixed)
  **Propulsion**               2-stage: 29mm booster (ejected) + 38mm sustainer (TVC-gimballed)
  **TVC Authority**            [±]{dir="rtl"}8° nozzle deflection, 2-axis cross-flexure gimbal
  **Active Fin Deflection**    [±]{dir="rtl"}25° per Ring 2 mid fin, individually servo-actuated on 7.4V HV (4 active fins). Ring 1 aft fins are passive (0° fixed).
  **Launch Mode**              1010/80-20 aluminum extrusion rail, 1.83m (6ft), near-vertical (85--90°)
  **Primary Structure**        PETG-CF 20% CF FDM printed, 3--4 perimeter walls
  **Avionics**                 3× custom 62mm circular PCBs: CCM (central) + ASAM-1 (mid fins) + ASAM-2 (TVC + sustainer relay; aft fins are passive)
  **Servo Spec (all)**         KST X08 Plus HV --- 7 total (4 mid fins + 2 TVC jetavane axes + 1 ceramic insert slide). Ring 1 aft fins are passive --- no servos.
  **Antenna**                  915MHz quarter-wave monopole on CCM, SMA pigtail, routed through tube wall
  **Recovery**                 Computer-triggered ejection charge, nose cone separation, 24in main chute
  **Datalink**                 915MHz LoRa --- Ebyte E22-900M22S, 22dBm, \~2km LoS
  **Target Altitude**          \~90--150m AGL (field-dependent)
  **Landing Mode**             Powered vertical descent, TVC + active fins
  **Total Mass (est.)**        \~620--680g all-up weight
  **Unit Build Cost (est.)**   \~\$525 USD (incl. PCB fab + SMT assembly; reduced from \$577 after removing 4 aft fin servos)
  ---------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------

1.2 Dimensional Scaling Rationale
---------------------------------

Scale factor k = 150mm / 70mm OD = 2.14. Scaled OAL = 2,500mm / 2.14 = 1,168mm (\~1,170mm with rail button standoffs). Scaled fin root chord aft ring = 200mm / 2.14 = 93mm. Scaled fin span aft ring = 150mm / 2.14 = 70mm. Scaled mid fin root chord = 100mm / 2.14 = 47mm.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

⚑ *All fin dimensions rounded to nearest 1mm for printability. Airfoil profile is a double-wedge at 4% t/c ratio. The 70mm body tube\'s internal 68mm ID gives 15mm radial clearance around the 38mm sustainer motor mount --- this annular space is the servo and gimbal bay.*
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

 

2\. Airframe & Structure

2.1 Body Tube
-------------

  ------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Body Tube Material**   PETG-CF 20% CF printed outer shell (2.4mm wall, 4 perimeter walls) bonded over 70mm OD / 68mm ID phenolic liner for structural backbone. Fin cans, centering rings, nose cone, TVC frame: all PETG-CF. Avionics sled, nose bay: PLA where heat not a concern.
  **Wall Thickness**       \~1.6mm nominal
  **OD**                   70.0mm
  **OAL (3 sections)**     \~1,170mm total
  **Forward Section**      \~270mm --- Nose cone bay + chute bay
  **Mid Section**          \~490mm --- CCM avionics sled + ASAM-1 + mid fin ring
  **Aft Section**          \~410mm --- ASAM-2 + sustainer motor + TVC gimbal + aft fin ring + booster
  **Section Coupling**     PETG-CF centering rings + 4× M3 nylon-tipped set screws per joint
  **Rail Interface**       2× 1010-profile rail buttons on aft section, 70mm OD compatible
  ------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

2.2 Nose Cone
-------------

  ------------------------ --------------------------------------------------------------------
  **Profile**              Von Karman ogive (Haack LV series)
  **Length**               234mm (500mm / 2.14)
  **Base Diameter**        70.0mm (flush with body tube OD)
  **Shoulder Length**      35mm slip-fit into forward section
  **Retention**            2× 3mm HDPE shear pins at 180° --- shear at 55--70N
  **Ejection Interface**   Aft face sealed; ejection charge vents into chute bay
  **Material**             PETG-CF 20% CF, 0.25mm layer height, 40% gyroid infill, 2.4mm wall
  ------------------------ --------------------------------------------------------------------

2.3 Fin Assemblies
------------------

### 2.3.1 Aft Stabilizer Ring --- Ring 1 (Passive, Fixed)

### Four fixed fins at the aft end of the aft section provide baseline aerodynamic stability in the yaw/pitch plane. Each fin is bonded directly into a radial slot in the PETG-CF aft fin can --- no servo, no hinge, no pivot pin. The fin roots are captured at 90° spacing around the motor tube by an epoxy bond line plus mechanical interlock geometry, freeing the annular space that previously held servo pockets for use by the TVC gimbal and wiring harness. Roll and primary pitch/yaw authority move entirely to Ring 2 and the jetavane TVC.

  ------------------------- ----------------------------------------------------------------------------
  **Quantity**              4, equally spaced at 90°
  **Root Chord**            93mm
  **Tip Chord**             47mm (tapered)
  **Span (from body)**      70mm
  **Leading Edge Sweep**    45°
  **Profile**               Double-wedge, 4% t/c, PETG-CF
  **Servo**                 None --- fixed bonded root (no actuator)
  **Servo Supply**          N/A --- fins are passive
  **Pivot Axis**            None --- fin root epoxy-bonded + mechanical interlock into PETG-CF fin can
  **Max Deflection**        0° (fixed)
  **Fin-Servo Clearance**   N/A --- annular bay freed; now used for TVC gimbal + harness routing
  **Thermal Shield**        0.2mm aluminum foil tape on PETG-CF fin can facing nozzle exit (unchanged)
  ------------------------- ----------------------------------------------------------------------------

### 

### 2.3.2 Mid Control Ring --- Ring 2 (Canard Position)

### Four all-moving fins positioned \~400mm forward of the aft fin ring provide primary pitch/yaw control authority at speed. Clocked 45° to Ring 1. Each fin is individually driven by a KST X08 Plus HV servo in the PETG-CF fin root housing in the mid-section body tube.

  ------------------------ -------------------------------------------------
  **Quantity**             4, equally spaced at 90°, clocked 45° to Ring 1
  **Root Chord**           47mm
  **Tip Chord**            23mm
  **Span (from body)**     35mm
  **Leading Edge Sweep**   40°
  **Servo**                KST X08 Plus HV --- 8g, ≥3.85 kg·cm @ 6V ×4
  **Servo Supply**         7.4V HV rail from ASAM-1 MT3608 boost converter
  **Pivot Axis**           50% chord
  **Max Deflection**       [±]{dir="rtl"}25°
  ------------------------ -------------------------------------------------

### 

### ⚑ *All 4 Ring 2 fin servos use identical KST X08 Plus HV units on a 7.4V rail. At this supply voltage each servo produces \~4.5 kg·cm stall torque --- well above the estimated 2.5--3.0 kg·cm peak aerodynamic hinge loads during boost transients at Mach 0.25--0.35.*

2.4 Structural Analysis (Simplified)
------------------------------------

  ---------------------------------------- -----------------------------------------------------------------------
  **Tensile Strength (PETG-CF printed)**   \~48 MPa XY plane, \~32 MPa Z
  **Flexural Modulus**                     \~3.8 GPa
  **Max Service Temp**                     75--85°C continuous (adequate for hobby motor plume proximity)
  **Motor Throat Mitigation**              Phenolic/aluminum motor retainer at nozzle exit; foil tape on fin can
  **Factor of Safety (launch shock)**      \>3.0 estimated at 18g peak axial acceleration
  **Fin flutter onset (est.)**             \>Mach 0.7 for Ring 1 full span --- safe in operational envelope
  ---------------------------------------- -----------------------------------------------------------------------

 

3\. Propulsion System

Two-stage propulsion. Stage 1 (29mm booster) accelerates the vehicle off the rail. At booster burnout, a delay element fires, the ejection ring ejects the booster casing rearward with a streamer, and the flight computer ignites the Stage 2 sustainer. Stage 2 (38mm sustainer) powers altitude hold, loiter, and the landing burn.

3.1 Stage 1 --- Booster Motor (29mm)
------------------------------------

  ------------------------------------ ------------------------------------------------------------------------------------------
  **Candidate Motor (Nominal)**        Cesaroni F39-6T (29mm, F class, \~6s delay, \~57N peak)
  **Candidate Motor (Conservative)**   Cesaroni F36-7T (29mm, F class, \~7s delay, \~40N peak)
  **Candidate Motor (High Alt.)**      AeroTech F52-5T (29mm, F class, \~5s delay)
  **Total Impulse Range**              80--120 N·s
  **Ejection Charge**                  Actuates booster ejection ring --- fractures HDPE shear pins, spring-ejects motor casing
  **Motor Retention**                  38/29mm reducer + friction fit + forward thrust ring --- no aft retainer (eject design)
  **Casing Recovery**                  900mm Kevlar cord + 500mm × 90mm nylon streamer
  ------------------------------------ ------------------------------------------------------------------------------------------

3.2 Stage 2 --- Sustainer Motor (38mm)
--------------------------------------

  ------------------------------ ------------------------------------------------------------------------
  **Motor Diameter**             38mm
  **Candidate (Nominal)**        AeroTech G76-10G (38mm, G class, \~10s burn, avg 76N, 637 N·s total)
  **Candidate (Conservative)**   AeroTech G54-10W (38mm, \~10s, avg 54N) --- lower T/W, easier TVC loop
  **Candidate (High Alt.)**      AeroTech G79-7W or Cesaroni G88-7 --- shorter burn, higher apogee
  **Avg Thrust to Weight**       \~8--11× vehicle weight --- manageable for TVC stabilization loop
  **Burn Time**                  \~7--10s --- covers loiter and landing burn initiation
  **Motor Retention**            Aeropack 38mm retainer ring threaded into aft PETG-CF motor mount
  **Ignition**                   E-match via ASAM-2 sustainer relay MOSFET, 1.5A firing current
  **Fire Timing**                CCM command at booster ejection + 0.2s
  ------------------------------ ------------------------------------------------------------------------

3.3 TVC Mount Design & Servo Integration
----------------------------------------

The TVC gimbal is the mechanical heart of the aft section. It must simultaneously: (1) gimbal the 38mm sustainer motor [±]{dir="rtl"}8° in pitch and yaw, (2) provide structural support for the motor through boost and loiter, and (3) co-exist in the aft section annulus with the fixed Ring 1 fin roots (bonded into the fin can; no servos). The following describes the physical arrangement.
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 3.3.1 Aft Section Annular Layout

### The 70mm body tube (68mm ID) encloses a 38mm motor mount tube. This creates a 15mm radial annular space between the motor OD (19mm radius) and the tube ID (34mm radius). This annulus is divided into two distinct functional zones around the circumference:

Zone A --- TVC Gimbal Frame (2 axes, \~180° arc): The outer PETG-CF gimbal ring occupies the inboard annular volume immediately aft of the mid-section coupling, spanning the aft \~80mm of the sustainer motor section. The pitch-axis servo and yaw-axis servo are bolted to the gimbal frame at 90° to each other, facing inboard toward the motor mount. Their output horns drive 2mm carbon fiber pushrods connected to M2 ball-link ends on the inner motor cradle.

Zone B --- Aft Fin Root Bonding Zone (4× fins at 90° spacing, fixed): The PETG-CF aft fin can has four radial slots machined into its OD at 90° spacing, clocked 45° from the TVC gimbal arms. Each Ring 1 fin root is inserted into its slot and captured by a high-strength epoxy bond line plus a mechanical keying feature (dovetail + shear pin) that carries aerodynamic load without a pivot. No servo, horn, pushrod, or hinge pin is present in this zone, which frees the radial annulus previously occupied by aft-fin servo pockets --- that volume is now available for TVC gimbal servicing, thermal standoff, and ASAM-2 harness routing.

  ----------------------------- --------------------------------------------------------------------------------------------------------------------------
  **Gimbal Type**               2-axis cross-flexure / pivot-bearing
  **Outer Ring Material**       PETG-CF, 4mm CF rod inserts in pivot bores
  **Inner Cradle**              PETG-CF, 38mm motor tube captured in M3-tensioned cradle
  **TVC Actuators**             2× KST X08 Plus HV --- Pitch axis (servo A) and Yaw axis (servo B)
  **Linkage**                   2mm CF pushrod + M2 hex ball-link ends (Dubro or equivalent)
  **Deflection Range**          [±]{dir="rtl"}8° per axis (mechanical hard stop at [±]{dir="rtl"}8.5°)
  **Total Vector Authority**    [±]{dir="rtl"}11.3° diagonal (vector sum of both axes)
  **TVC Servo Supply**          7.4V HV from ASAM-2 MT3608 boost converter
  **TVC Torque Demand**         \~3.5--5.0 kg·cm peak at 38mm motor (\~60--80N thrust × 15--20mm moment arm)
  **TVC Servo Margin**          KST X08 Plus HV delivers 5.3 kg·cm @ 8.4V --- positive margin
  **Mounting**                  4× M3 brass inserts into aft centering ring
  **Aft Fin Servo Pockets**     None --- aft fins are passive; roots bonded directly into radial slots in PETG-CF fin can (no servo hardware in annulus)
  **Aft Fin Linkage**           None --- fin root captured by epoxy bond line + dovetail/shear-pin mechanical keying; no pushrod or hinge pin
  **Motor-Servo Thermal Gap**   Air gap + 0.2mm aluminum foil tape; PETG-CF structure between servo and nozzle exit
  ----------------------------- --------------------------------------------------------------------------------------------------------------------------

⚑ *With Ring 1 passive, the 15mm radial annulus now carries only the TVC gimbal frame, its two servos, and wiring. The TVC servos (KST X08 Plus HV) are still the sizing driver --- body 8mm × 22mm × 26mm (T × W × H). In the radial orientation: 8mm thickness fits in 15mm radial space with 7mm margin --- split \~3.5mm either side for PETG-CF mounting wall and thermal gap. TVC servo wiring exits tangentially along the tube ID to ASAM-2.*

3.4 Booster Ejection Ring
-------------------------

Ejection spring: 3-turn 0.9mm stainless compression spring, preloaded 6N

Shear pins: 2× 2mm HDPE pins, shear at \~35N axial

Streamer: 500mm × 90mm ripstop nylon, fluorescent orange

Attachment: 900mm Kevlar cord to motor casing forward lip

Separation detection: CCM monitors barometric delta-P spike at ejection event

3.5 Motor Selection Matrix
--------------------------

  --------------- -------------------- ---------------------- ----------------- ----------------------------
  **Scenario**    **Booster (29mm)**   **Sustainer (38mm)**   **Est. Apogee**   **Notes**
  Conservative    F36-7T               G54-10W                \~85m             Low ceiling, easy TVC loop
  Nominal         F39-6T               G76-10G                \~120m            Recommended first flight
  High Altitude   F52-5T               G79-7W                 \~175m            High-ceiling field only
  --------------- -------------------- ---------------------- ----------------- ----------------------------

 

4\. Avionics Architecture --- 3-PCB Distributed Flight Computer

The avionics stack consists of three custom 62mm circular PCBs. The Central Command Module (CCM) is the primary flight computer, guidance law executor, and datalink node. Two Auxiliary Sensor & Actuator Modules (ASAM-1 and ASAM-2) each independently manage sensor fusion, servo driving, and power for their respective fin rings. ASAM-2 additionally drives the two TVC gimbal servos and the sustainer ignition relay.

Each ASAM connects to the CCM via a single JST-GH 8-pin ribbon cable carrying UART (commands), SPI (IMU data), I2C (baro polling), and power ground reference. Each board has its own LiPo --- power is not shared across the inter-board bus, only ground reference.

⚑ *All boards: 62mm diameter, 2-layer FR4 1.6mm, ENIG finish, EasyEDA design, JLCPCB fabrication. 3mm keepout from board edge; 4× M2.5 mounting holes at 52mm bolt circle. Boards stack on a PETG-CF sled inside the mid-section tube, locked with set screws.*

4.1 Board Overview
------------------

  ----------- ----------------------- ---------------------------------------------------------------------- -------------- -----------
  **Board**   **Designation**         **Primary Role**                                                       **Diameter**   **MCU**
  CCM         Central Command         Flight computer, guidance, LoRa datalink, 3× pyro, IMU, baro           62mm           RP2040
  ASAM-1      Mid Ring Module         4× mid fin servos (Ring 2), redundant IMU+baro, 1S LiPo                62mm           STM32F411
  ASAM-2      Aft Ring + TVC Module   4× aft fin servos (Ring 1) + 2× TVC servos, sustainer relay, 1S LiPo   62mm           STM32F411
  ----------- ----------------------- ---------------------------------------------------------------------- -------------- -----------

4.2 CCM --- Central Command Module
----------------------------------

The CCM is the flight computer, guidance law executor, and RF link hub. All three pyrotechnic channels are on this board. The LoRa antenna (915MHz quarter-wave monopole) is connected via SMA pigtail and exits through a 4mm hole in the tube wall sealed with silicone RTV.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 4.2.1 CCM --- Bill of Materials (Board-Level)

  ---------------- ---------------------------- ----------------- ----------------- -----------------------------------
  **Designator**   **Component**                **Package**       **Source**        **Function**
  U1               RP2040                       QFN-56            LCSC / WeAct      Primary MCU, dual M0+ 133MHz
  U2               W25Q128JVSIQ                 SOIC-8            LCSC              16MB QSPI Flash --- telemetry log
  U3               ICM-42688-P                  LGA-14            LCSC / Sparkfun   Primary IMU --- SPI 32kHz ODR
  U4               BMP388                       LGA-8             LCSC              Primary barometer --- I2C 200Hz
  U5               Ebyte E22-900M22S            SMD module        Ebyte / LCSC      LoRa 915MHz, SX1268, 22dBm
  U6               TLV62569                     SOT-23-5          LCSC              3.3V 600mA buck for logic
  Q1--Q3           IRFZ44N (×3)                 TO-220 or D2PAK   LCSC              Pyro MOSFET channels ×3
  J1               JST-GH 8-pin                 Through-hole      JST               ASAM-1 inter-board connector
  J2               JST-GH 8-pin                 Through-hole      JST               ASAM-2 inter-board connector
  J3               SMA Edge-mount               PCB mount         Molex             LoRa antenna pigtail
  J4               XT30-M                       Through-hole      Amass             1S LiPo 850mAh battery
  J5               2-pin screw terminal         Through-hole      Generic           Physical arming switch
  J6--J8           2-pin screw terminals (×3)   Through-hole      Generic           Pyro channel e-match outputs
  SW1              TC2030 debug header          SMD 6-pin         Tag-Connect       SWD programming + UART boot
  LED1--3          Bicolor LED (×3)             0805              LCSC              Pyro continuity indication
  ---------------- ---------------------------- ----------------- ----------------- -----------------------------------

### 

### 4.2.2 CCM --- Connectivity & Pin Assignment

  -------------------------- ----------------- ----------------- ---------------------------------------------------
  **Signal**                 **RP2040 GPIO**   **Peripheral**    **Notes**
  IMU\_CS                    GPIO5             ICM-42688-P       SPI0 chip select --- IMU
  IMU\_SCK / MOSI / MISO     GPIO6/7/4         ICM-42688-P       SPI0 @ 4MHz
  BARO\_SDA / SCL            GPIO8/9           BMP388            I2C1 @ 400kHz
  LORA\_CS                   GPIO13            E22-900M22S       SPI1 chip select
  LORA\_SCK/MOSI/MISO        GPIO14/15/12      E22-900M22S       SPI1 @ 2MHz
  LORA\_BUSY / DIO1 / NRST   GPIO16/17/18      E22-900M22S       RF handshake lines
  ASAM1\_TX / RX             GPIO0/1           ASAM-1 UART       UART0 115200 baud --- commands / status
  ASAM2\_TX / RX             GPIO2/3           ASAM-2 UART       UART1 115200 baud --- commands / status
  PYRO\_CH1                  GPIO20            IRFZ44N Q1        Nose chute e-match fire
  PYRO\_CH2                  GPIO21            IRFZ44N Q2        Sustainer ignition relay command to ASAM-2
  PYRO\_CH3                  GPIO22            IRFZ44N Q3        Spare / backup chute
  ARM\_SENSE                 GPIO26 ADC0       Arm switch        Low = disarmed, High = armed (hardware interlock)
  VBAT\_SENSE                GPIO27 ADC1       Voltage divider   100k/47k --- CCM LiPo monitor
  -------------------------- ----------------- ----------------- ---------------------------------------------------

### 

### 4.2.3 CCM --- LoRa Antenna

### The LoRa antenna is a 77mm (quarter-wave at 915MHz) wire monopole soldered to the SMA pigtail center pin, routed axially along the body tube ID and exiting through a 4mm hole in the tube wall. The hole is sealed with silicone RTV after installation. The SMA edge-mount connector sits at the 12 o\'clock position on the board edge for straight cable routing.

  ------------------- -----------------------------------------------------------------------------
  **Module**          Ebyte E22-900M22S (SX1268, 22dBm EIRP, -148dBm sensitivity)
  **Frequency**       915MHz ISM band (US); 868MHz variant for EU
  **Antenna Type**    Quarter-wave wire monopole, 77mm length, 50Ω
  **Connector**       SMA edge-mount on CCM → SMA pigtail → antenna wire
  **Exit Routing**    4mm hole in tube wall at CCM position, sealed with silicone RTV
  **Uplink Frame**    Binary: target\_alt (int16) + abort\_flag (bool) + arm\_land (bool) + CRC16
  **Downlink Rate**   10Hz, 64-byte frames: altitude, velocity, attitude, fin positions, battery
  **Range**           \~2km LoS @ SF9, 125kHz BW --- adequate for \<200m AGL
  ------------------- -----------------------------------------------------------------------------

### 

4.3 ASAM-1 --- Mid Ring Controller
----------------------------------

ASAM-1 manages the four mid-ring (Ring 2) fin servos and provides the CCM with a redundant IMU and barometer. It accepts servo deflection commands from the CCM over UART and outputs 4× 50Hz PWM channels to the KST X08 Plus HV servos on a 7.4V HV rail generated by an MT3608 boost converter from the 1S LiPo.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 4.3.1 ASAM-1 --- Bill of Materials (Board-Level)

  ---------------- ------------------------- -------------- ----------------- --------------------------------------------
  **Designator**   **Component**             **Package**    **Source**        **Function**
  U1               STM32F411CEU6             UFQFPN-48      LCSC              MCU --- Cortex-M4 100MHz FPU
  U2               ICM-42688-P               LGA-14         LCSC / Sparkfun   Redundant IMU --- SPI 32kHz
  U3               MS5611                    SMD-8          LCSC              Redundant barometer --- SPI 150Hz
  U4               INA219                    SOT-23-8       LCSC              Servo current monitor on 7.4V rail
  U5               TLV62569                  SOT-23-5       LCSC              3.3V 600mA buck for logic
  U6               MT3608                    SOT-23-6       LCSC              Boost converter --- 1S LiPo → 7.4V HV rail
  J1               JST-GH 8-pin              Through-hole   JST               CCM inter-board ribbon
  J2--J5           JR/Futaba 3-pin (×4)      Through-hole   Generic           Servo outputs --- Ring 2 fins 1--4
  J6               XT30-M                    Through-hole   Amass             1S LiPo 1000mAh input
  R1--R4           10kΩ pull-up (×4)         0402           LCSC              I2C pull-ups on SDA/SCL
  C1--C4           470μF electrolytic (×4)   Radial         LCSC              Bulk cap on 7.4V servo rail
  C5--C20          100nF ceramic (×16)       0402           LCSC              Decoupling on all IC power pins
  SW1              TC2030                    SMD 6-pin      Tag-Connect       SWD debug + UART bootloader
  ---------------- ------------------------- -------------- ----------------- --------------------------------------------

### 

### 

### 4.3.2 ASAM-1 --- Servo PWM Output Mapping

  -------------------- -------------------- ----------------------------- -------------------------------------------
  **Connector**        **STM32 Timer Ch**   **Fin**                       **Control Function**
  J2 --- Servo Out 1   TIM1\_CH1 (PA8)      Ring 2, Fin 1 (North, 0°)     Pitch + (up fin, increase nose-up moment)
  J3 --- Servo Out 2   TIM1\_CH2 (PA9)      Ring 2, Fin 2 (East, 90°)     Yaw + (right fin, yaw right)
  J4 --- Servo Out 3   TIM1\_CH3 (PA10)     Ring 2, Fin 3 (South, 180°)   Pitch - (down fin, increase nose-down)
  J5 --- Servo Out 4   TIM1\_CH4 (PA11)     Ring 2, Fin 4 (West, 270°)    Yaw - (left fin, yaw left)
  -------------------- -------------------- ----------------------------- -------------------------------------------

### 

### ⚑ *50Hz PWM frame, 1000--2000μs pulse width. 1500μs = neutral. Roll is commanded by differential deflection on all 4 fins simultaneously (opposing pairs deflect opposite directions). PID mixing table in CCM firmware.*

4.4 ASAM-2 --- Aft Ring + TVC Controller
----------------------------------------

ASAM-2 is the TVC + sustainer controller. It drives 2 servo channels (jetavane TVC pitch and yaw axes) plus the optional ceramic-slide servo, and hosts the sustainer motor ignition relay (IRFZ44N + optocoupler isolation) fired by CCM UART command. It is otherwise identical to ASAM-1 in MCU, sensor suite, and power architecture. The 1S 1200mAh LiPo is retained --- with Ring 1 passive, ASAM-2\'s peak servo current draw drops from \~9A to \~3A, leaving substantial battery margin for standby and contingency loads.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 4.4.1 ASAM-2 --- Bill of Materials (Board-Level)

  ---------------- ------------------------- ----------------- ----------------- -----------------------------------------------------------------
  **Designator**   **Component**             **Package**       **Source**        **Function**
  U1               STM32F411CEU6             UFQFPN-48         LCSC              MCU --- Cortex-M4 100MHz FPU
  U2               ICM-42688-P               LGA-14            LCSC / Sparkfun   Redundant IMU --- SPI 32kHz
  U3               MS5611                    SMD-8             LCSC              Redundant barometer --- SPI 150Hz
  U4               INA219                    SOT-23-8          LCSC              Servo current monitor on 7.4V rail
  U5               TLV62569                  SOT-23-5          LCSC              3.3V 600mA buck for logic
  U6               MT3608                    SOT-23-6          LCSC              Boost converter --- 1S LiPo → 7.4V HV rail
  U7               TPS5430                   TO-263-7          LCSC              5V 3A buck for ASAM-2 logic (extra headroom)
  U8               PC817 optocoupler         DIP-4             LCSC              Sustainer relay isolation
  Q1               IRFZ44N                   TO-220 or D2PAK   LCSC              Sustainer e-match MOSFET relay
  J1               JST-GH 8-pin              Through-hole      JST               CCM inter-board ribbon
  J2--J3           JR/Futaba 3-pin (×2)      Through-hole      Generic           Servo outputs --- TVC pitch (J2) & yaw (J3) \[jetavane gimbal\]
  J4               JR/Futaba 3-pin (×1)      Through-hole      Generic           Servo output --- ceramic slide vane (TVC throttle authority)
  J5               XT30-M                    Through-hole      Amass             1S LiPo 1200mAh input
  J6               2-pin screw terminal      Through-hole      Generic           Sustainer e-match output
  J7               Reed switch header        2-pin             Generic           Booster eject detect (magnet on casing)
  C1--C3           470μF electrolytic (×3)   Radial            LCSC              Bulk cap on 7.4V rail (sized for 3 TVC servos)
  SW1              TC2030                    SMD 6-pin         Tag-Connect       SWD debug + UART bootloader
  ---------------- ------------------------- ----------------- ----------------- -----------------------------------------------------------------

### 

### 4.4.2 ASAM-2 --- Servo PWM Output Mapping

  ---------------------- -------------------- ---------------------------------- --------------------------------------------------------------------------
  **Connector**          **STM32 Timer Ch**   **Servo / Fin**                    **Control Function**
  J2 --- TVC Pitch       TIM2\_CH1 (PA0)      TVC Servo A (pitch axis)           Motor pitch deflection --- CCM pitch cmd
  J3 --- TVC Yaw         TIM2\_CH2 (PA1)      TVC Servo B (yaw axis)             Motor yaw deflection --- CCM yaw cmd
  J4 --- Ceramic Slide   TIM2\_CH3 (PA2)      TVC Servo C (ceramic slide vane)   Throttle / ΔV authority --- vane insertion reduces nozzle effective area
  ---------------------- -------------------- ---------------------------------- --------------------------------------------------------------------------

### 

4.5 PCB Fabrication & Cost
--------------------------

  ---------------------------------------------- --------------------------------------------------------------------
  **Fab House**                                  JLCPCB (preferred) --- 5 business day lead time standard
  **Layer Stack**                                2-layer FR4, 1.6mm, ENIG finish
  **Board Outline**                              62mm diameter circular --- EasyEDA DXF boundary
  **Minimum Trace / Space**                      0.15mm / 0.15mm (standard process, adequate for all signals)
  **Quantity per Order**                         5× of each design (minimum JLCPCB order = 5 pcs)
  **CCM PCB Bare (5pcs)**                        \~\$8--10 USD at JLCPCB
  **ASAM-1 PCB Bare (5pcs)**                     \~\$8--10 USD
  **ASAM-2 PCB Bare (5pcs)**                     \~\$8--10 USD
  **JLCPCB SMT Assembly --- CCM**                \~\$35--45 USD (RP2040, ICM-42688-P, BMP388, passives, E22 module)
  **JLCPCB SMT Assembly --- ASAM-1**             \~\$25--35 USD (STM32F411, ICM-42688-P, MS5611, passives)
  **JLCPCB SMT Assembly --- ASAM-2**             \~\$30--40 USD (STM32F411, ICM-42688-P, MS5611, passives, opto)
  **Total PCB + Assembly Cost (1 set)**          \~\$114--145 USD
  **Subsequent Sets (bare PCBs already made)**   \~\$60--80 USD (components only)
  ---------------------------------------------- --------------------------------------------------------------------

⚑ *ICM-42688-P, BMP388, MS5611, STM32F411CEU6, and RP2040 are all available in the JLCPCB parts library for SMT assembly. IRFZ44N (TO-220) and JR servo connectors are through-hole --- hand solder after SMT reflow. Use JLCPCB \'Economic\' SMT for lowest cost on standard passives; \'Standard\' SMT for the QFN MCU packages.*
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

 

5\. Flight Profile & State Machine

5.1 Mission Phases
------------------

  -------- ------------------ ----------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------
  **\#**   **Phase**          **Duration**      **Description**
  0        SAFE               Pre-launch        Rail mounted, arming switch OFF. All pyro channels disabled, servos neutral.
  1        ARMED              T-30s to T0       Switch ON. CCM boots, IMU/baro calibration, GCS link confirmed, pyro continuity verified, target altitude uplinked.
  2        BOOST              T+0 to \~T+2.5s   Booster ignites. Vehicle accelerates off rail. Fins neutral on rail. TVC inactive (booster not gimballed).
  3        RAIL CLEAR         T+2.5 to \~T+5s   Rail clearance confirmed. Fin authority increases with airspeed. ASAM-1/2 activate fin loops. CCM runs attitude hold --- vertical via fin differential.
  4        COAST / EJECT      T+5 to \~T+7s     Booster burnout + delay. Ejection ring fires. Casing deploys streamer. CCM sends sustainer ignition command to ASAM-2 at eject+0.2s.
  5        SUSTAINER LOITER   T+7 to \~T+17s    Sustainer ignites. TVC + all 4 mid fins active (aft fins are fixed/passive). CCM altitude hold: targets uplinked AGL (90--150m). Loiter 10--20s.
  6        POWERED DESCENT    T+17 to \~T+24s   CCM initiates landing burn. TVC + fins maintain vertical. Decelerates from \~5m/s at 15m AGL to \<1m/s at touchdown.
  7        TOUCHDOWN          T+24s             Accel spike \>10g axial. CCM logs event, disarms all pyro, servos neutral.
  8        ABORT              Any phase         GCS abort command OR attitude error \>45° for \>0.5s OR altitude runaway: nose chute fires, ballistic recovery.
  -------- ------------------ ----------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------

5.2 Guidance & Control Laws
---------------------------

### 5.2.1 Attitude Hold

  --------------------------- ------------------------------------------------------------------------------------------
  **Outer Loop (Altitude)**   PID on altitude error → target pitch/yaw angle command
  **Inner Loop (Attitude)**   PID on attitude error (quaternion → Euler) → fin + TVC deflection commands
  **Fin Mixing**              Pitch: +/- symmetric top/bottom; Yaw: +/- symmetric left/right; Roll: differential all 4
  **TVC Mixing**              Pitch: TVC Servo A; Yaw: TVC Servo B --- decoupled command matrix
  **Update Rate**             500Hz ASAM MCUs (servo interpolated at 50Hz PWM); 100Hz CCM state machine
  **Filter**                  Mahony AHRS for attitude; complementary filter (gyro + baro) for altitude rate
  **IMU Fusion**              CCM averages ASAM-1 and ASAM-2 IMU quaternions; discards outlier if \>3° discrepancy
  --------------------------- ------------------------------------------------------------------------------------------

### 

### 5.2.2 Powered Descent Guidance

### The landing burn uses a simplified 1D guidance law. Since the motor is unthrottlable, burn start time T\_land is computed from current altitude, target ground level, and a pre-set nominal sink rate (\~2.5m/s). The TVC and fins maintain verticality throughout. Rev A uses a lookup-table burn profile tuned in OpenRocket simulation.

###  

6\. OpenRocket Model Parameters

The accompanying XRIM117\_PTD\_PDR002\_70mm.ork file contains the full OpenRocket model with all three motor configurations (Conservative, Nominal, High Altitude) pre-loaded. Import into OpenRocket 23.09 or later. All mass overrides are set per the values below.

6.1 Component Stack
-------------------

  --------------------------- ------------------------------ ----------------- ------------------- -----------------------
  **Component**               **Type in OR**                 **Length (mm)**   **Diameter (mm)**   **Mass Override (g)**
  Von Karman Nose Cone        Nose Cone, Haack LV            234               70.0 OD             42
  Chute Bay Tube              Body Tube                      100               70.0 OD             28 (incl. chute)
  CCM Avionics Sled           Mass Component                 ---               ---                 45
  Mid Fin Ring + ASAM-1       Body Tube + Trap. Fin Set ×4   150               70.0 OD             70
  Sustainer Section           Body Tube                      340               70.0 OD             80
  Sustainer Motor (38mm)      Motor Mount 38mm               ---               ---                 OR motor data
  TVC Gimbal Assembly         Mass Component                 ---               ---                 30
  Aft Fin Ring + Motor Tube   Body Tube + Fin Set ×4         250               70.0 OD             95
  Booster Motor (29mm)        Motor Mount 29mm (inner)       ---               ---                 OR motor data
  Booster Ejection Ring       Mass Component                 ---               ---                 16
  --------------------------- ------------------------------ ----------------- ------------------- -----------------------

6.2 Stability Targets
---------------------

  --------------------------------- ---------------------------------------------------
  **Target Stability Margin**       1.5--2.5 calibers at launch (loaded)
  **Caliber**                       70.0mm
  **Acceptable CP position**        \>105mm aft of CG
  **OR Simulation Atmosphere**      ISA standard, field elevation input at launch day
  **Cd (subsonic estimate)**        \~0.42 (Barrowman + OR drag model)
  **Cp travel (OR output)**         Verify \<0.5 caliber shift launch to max-q
  **Stability (empty sustainer)**   Verify \>1.0 caliber for recovery phase
  --------------------------------- ---------------------------------------------------

 

7\. Recovery System

7.1 Primary Recovery --- Nose Cone Ejection
-------------------------------------------

  ------------------------------ ----------------------------------------------------------------------
  **Ejection Charge Material**   FFFFg black powder (Goex or equivalent)
  **Charge Mass**                0.45g nominal --- ground test at 0.35g and 0.55g before first flight
  **Charge Housing**             Phenolic cap epoxied to aft bulkhead of chute bay
  **Ignition**                   Solar igniter via CCM pyro CH1 MOSFET
  **Bay Sealing**                O-ring on nose shoulder (Buna-N \#222, 3/16 cross-section)
  **Shear Pins**                 2× 3mm HDPE rod, 10mm long --- shear at 55--70N
  **Recovery Harness**           800mm 9mm tubular Kevlar, rated \>400N
  **Parachute**                  24in (610mm) ripstop nylon, 6-gore round
  **Target Descent Rate**        \<5m/s at \~630g vehicle mass --- achieved with 24in at sea level
  ------------------------------ ----------------------------------------------------------------------

7.2 Booster Section Recovery
----------------------------

  ---------------------- ---------------------------------------------------------------------------
  **Streamer**           500mm × 90mm ripstop nylon, fluorescent orange
  **Attachment**         900mm Kevlar cord to motor casing forward lip
  **Deploy Mechanism**   Booster motor ejection charge --- passive, no flight computer involvement
  **Descent Rate**       \~8--12m/s with streamer at \~100g casing mass
  ---------------------- ---------------------------------------------------------------------------

 

8\. Ground Support Equipment & Launch Infrastructure

8.1 Ground Station (GCS)
------------------------

  --------------------- --------------------------------------------------------------------------------------------
  **Hardware**          Raspberry Pi 4 (4GB) + 7in touchscreen or laptop
  **RF Module**         Ebyte E22-900M22S USB dongle (SX1268, 915MHz) + 915MHz whip antenna
  **Software**          Python 3 GCS (custom) --- displays altitude, attitude, fin positions, battery, motor state
  **Uplink Controls**   Slider: target altitude (0--200m), Button: ABORT (fires chute), Button: ARM LANDING
  **Logging**           SQLite database, all telemetry at 10Hz, flight replay capability
  **Link Range**        \~2km LoS --- adequate for all planned flight envelopes
  --------------------- --------------------------------------------------------------------------------------------

8.2 Launch Rail Configuration
-----------------------------

  ----------------------- -----------------------------------------------------------------------
  **Rail**                1010 Aluminum extrusion, 1.83m (6ft), 10mm × 10mm T-slot profile
  **Rail Buttons**        2× 1010-profile rail buttons on aft section --- 70.0mm OD compatible
  **Launch Controller**   12V battery + relay box + continuity light + key-arm switch
  **Pad Elevation**       85--90° from horizontal --- near-vertical, 2--3° into prevailing wind
  **Blast Shield**        Optional 3mm aluminum plate behind booster section
  **Recovery Zone**       Minimum 75m radius cleared downrange
  ----------------------- -----------------------------------------------------------------------

8.3 Pre-Flight Checklist
------------------------

Structural: all section couplings torqued, set screws seated, fins secure, TVC gimbal range clear

Pyro: continuity check on all channels via CCM LED indicators (green = OK on CH1, CH2, CH3)

Avionics: CCM boot confirmed (LED sequence), ASAM-1/2 heartbeat received by CCM

Sensors: baro reads field elevation [±]{dir="rtl"}5m, IMU static noise \<0.1°/s on all 3 boards

Datalink: GCS telemetry stream confirmed at 10Hz, uplink echo verified (send test altitude, confirm CCM echoes)

Servos: full sweep test via GCS --- all 4 mid fins deflect [±]{dir="rtl"}25°, TVC deflects [±]{dir="rtl"}8° on both axes

Motors: booster motor installed + igniter inserted + continuity checked; sustainer motor installed + igniter inserted + continuity to ASAM-2 relay verified

Rail: vehicle on rail, rail buttons seated and travel tested, launch controller continuity confirmed

Target altitude: set in GCS, uplinked to CCM, confirmed on GCS telemetry display

Range clear: 75m radius, FAA notification if required (\>400ft AGL)

ARM: physical arming switch ON, GCS shows ARMED state, all pyro channels green

9\. Bill of Materials & Cost Estimate

  ------------------------------------------------------------------------ -------------------------------- --------- ------------- --------------
  **Item**                                                                 **Source**                       **Qty**   **Unit \$**   **Total \$**
  70mm OD phenolic/fiberglass body tube (1.2m)                             Apogee / LOC Precision           1         \$22          \$22
  PETG-CF filament 20% CF (750g)                                           eSUN / Polymaker                 1         \$32          \$32
  KST X08 Plus HV micro-servo (7 total --- 4 mid fins + 2 TVC + 1 slide)   HobbyKing / Aeroworks            7         \$13          \$91
  AeroTech G76-10G 38mm sustainer motor                                    Local rocketry club / AeroTech   2         \$38          \$76
  Cesaroni F39-6T 29mm booster motor                                       Local rocketry club              2         \$24          \$48
  Aeropack 38mm motor retainer                                             Aeropack / Apogee                1         \$18          \$18
  RP2040 (WeAct bare board)                                                WeAct / LCSC                     2         \$3           \$6
  STM32F411CEU6                                                            LCSC                             3         \$4           \$12
  ICM-42688-P IMU (×3 boards)                                              LCSC / Sparkfun                  3         \$6           \$18
  BMP388 barometer (CCM)                                                   LCSC                             1         \$3           \$3
  MS5611 barometer (×2, ASAM-1/2)                                          LCSC                             2         \$4           \$8
  Ebyte E22-900M22S LoRa (CCM + GCS dongle)                                LCSC / Ebyte                     2         \$9           \$18
  MT3608 boost converter module ×4                                         AliExpress                       4         \$2           \$8
  IRFZ44N MOSFET (pyro ×3 + sustainer relay)                               LCSC                             4         \$0.60        \$2.40
  INA219 current sensor ×2 (ASAM-1/2)                                      LCSC                             2         \$1.50        \$3
  PC817 optocoupler (sustainer relay)                                      LCSC                             2         \$0.40        \$0.80
  1S 850mAh LiPo (CCM)                                                     Turnigy / GNB                    1         \$7           \$7
  1S 1000mAh LiPo (ASAM-1)                                                 Turnigy / GNB                    1         \$8           \$8
  1S 1200mAh LiPo (ASAM-2)                                                 Turnigy / GNB                    1         \$9           \$9
  PCB bare fabrication --- CCM (5pcs, 62mm circular)                       JLCPCB                           1 set     \$9           \$9
  PCB bare fabrication --- ASAM-1 (5pcs)                                   JLCPCB                           1 set     \$9           \$9
  PCB bare fabrication --- ASAM-2 (5pcs)                                   JLCPCB                           1 set     \$9           \$9
  SMT assembly --- CCM (RP2040, ICM, BMP388, passives, E22)                JLCPCB                           1 set     \$40          \$40
  SMT assembly --- ASAM-1 (STM32, ICM, MS5611, passives)                   JLCPCB                           1 set     \$30          \$30
  SMT assembly --- ASAM-2 (STM32, ICM, MS5611, passives, opto)             JLCPCB                           1 set     \$35          \$35
  JST-GH 8-pin connectors + ribbon cable                                   AliExpress                       1 set     \$6           \$6
  SMA pigtail + 915MHz antenna wire                                        AliExpress                       1         \$4           \$4
  24in parachute                                                           Apogee / Fruity Chutes           1         \$24          \$24
  Kevlar shock cord + misc hardware                                        Local                            1         \$15          \$15
  Black powder FFFFg 1oz                                                   Local gun shop                   1         \$6           \$6
  1010 rail 6ft section                                                    Misumi / 80/20                   1         \$22          \$22
  2mm CF pushrod, M2 ball links, M3 hardware                               HobbyKing / AliExpress           1 set     \$8           \$8
  Miscellaneous (epoxy, wire, foil tape, fasteners)                        Local                            1         \$25          \$25
  **TOTAL ESTIMATED BUILD COST**                                                                                                    **\~\$632**
  ------------------------------------------------------------------------ -------------------------------- --------- ------------- --------------

⚑ *PCB fab + SMT assembly is \~\$132 of the total --- a one-time cost. Subsequent builds (bare PCBs already ordered in 5-packs) reduce to \~\$248. Motors are the largest recurring cost at \$124 per 2-flight set. Servo cost drops to \$91 for 7 units (4 mid fins + 2 TVC axes + 1 ceramic slide) now that Ring 1 aft fins are passive --- a \$52 saving vs. the original 10-servo configuration with no loss of TVC or primary pitch/yaw authority.*

10\. Recommended Build Sequence

Phase 1 --- Design & Fabrication (Weeks 1--3)
---------------------------------------------

Model full airframe in OpenRocket using accompanying .ork file; verify stability margin 1--2 cal across motor burn

CAD all PETG-CF parts: nose cone, fin cans, centering rings, TVC gimbal frame, motor cradle, avionics sled

Design CCM, ASAM-1, ASAM-2 PCBs in EasyEDA --- 62mm circular outline, 2-layer, ENIG

Order PCBs from JLCPCB with SMT assembly for MCUs and surface-mount ICs

Order all electronics from LCSC/AliExpress, servos from HobbyKing, motors from local rocketry club

Phase 2 --- Print & Mechanical (Weeks 3--5)
-------------------------------------------

Print all PETG-CF parts at 0.2mm layer height, 3--4 perimeter walls, 40--60% gyroid infill

Test fit body tube couplings; sand shoulder fits to 0.1--0.2mm clearance

Bond aft fin can to body tube with 5-min epoxy + CA fillet; cure 24hr before loading fins

Fabricate and test TVC gimbal: assemble outer frame + inner cradle, verify [±]{dir="rtl"}8° range on both axes with no binding

Verify fin servo pocket fit: servo body (8mm) must sit flush in PETG-CF pocket with 3--4mm thermal gap to motor tube

Test booster ejection ring: spring preload, shear pin shear load, streamer deploy sequence

Phase 3 --- Electronics (Weeks 5--7)
------------------------------------

Receive PCBs from JLCPCB; inspect SMT assembly --- check RP2040, STM32F411, ICM-42688-P solder joints under magnification

Hand solder through-hole: IRFZ44N, JST-GH connectors, servo 3-pin headers, XT30 battery connectors,

Flash bootloader and test firmware on CCM, ASAM-1, ASAM-2 individually over SWD

Verify I2C/SPI/UART inter-board communication on bench with all 3 boards connected via JST-GH ribbons

Calibrate all 3 IMUs and barometers on level surface; verify baro cross-check on CCM shows \<2m disagreement between boards

Bench-test all 10 servo channels: 8 fins at [±]{dir="rtl"}25°, 2 TVC axes at [±]{dir="rtl"}8° --- all on 7.4V HV rail

Test pyro channels (without charges): all 3 CCM IRFZ44N MOSFETs fire on command, ASAM-2 sustainer relay fires on CCM UART command

Test datalink: GCS receives 10Hz telemetry, uplink target altitude command echoes on CCM display

Phase 4 --- Integration & Ground Testing (Weeks 7--8)
-----------------------------------------------------

Install avionics sled in body tube; route JST-GH ribbon cables, servo wiring, and LoRa antenna pigtail

Route antenna wire through 4mm hole in tube wall; seal with silicone RTV; verify SMA connection torque

Static servo sweep in assembled vehicle: command full deflection on all 10 channels --- no mechanical binding, no cable snagging

Ejection charge ground test: load 0.45g BP in nose bay, fire on ground, verify nose separation and chute deployment within 200ms

TVC range test with motor installed (static): command [±]{dir="rtl"}8° pitch and yaw on TVC servos with motor in gimbal --- verify no binding at full deflection under motor weight

Full pre-flight systems test: ARM switch ON, igniters connected (no propellant), all GCS commands exercise correctly

Phase 5 --- Rail-Launch Flight Tests (Week 9+)
----------------------------------------------

Flight 1: Booster only (no sustainer motor installed) --- verify rail clearance, stability, booster ejection, chute deployment and recovery

Flight 2: Both stages, chute recovery (no landing burn) --- verify staging event, sustainer ignition timing, altitude hold behavior

Flight 3: Full profile with landing burn at conservative altitude (40m target) --- verify entire 8-phase state machine

Subsequent flights: increase target altitude in 15--20m increments, refine PID gains, log and analyze TVC authority vs fin authority split
