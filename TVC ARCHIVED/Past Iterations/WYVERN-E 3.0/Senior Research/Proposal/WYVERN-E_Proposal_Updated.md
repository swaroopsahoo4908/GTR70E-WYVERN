# WYVERN-E: Engineering Design and Experimental Validation of Autonomous Magnetic Thrust-Vector Control, Additive Materials, Aerodynamic Optimization, and Wind Tunnel Evaluation in a Two-Stage Subscale-Demonstrator Guided Rocket

Allison Hong, Chris Liu, Swaroop K. Sahoo

April 20th, 2026 · Revised June 2026 (Architecture Rev PDR-005)

---

## Student Information

**Student Names:** Swaroop Sahoo, Chris Liu, Allison Hong

**Project Title:** WYVERN-E: Engineering Design and Experimental Validation of Autonomous Magnetic Thrust-Vector Control, Additive Materials, Aerodynamic Optimization, and Wind Tunnel Evaluation in a Two-Stage Subscale-Demonstrator Guided Rocket

**Research Pathway:** Engineering/Innovation Design

**Intended Majors:**

- *Swaroop Sahoo*: Electrical Engineering with Aerospace Engineering Minor
- *Chris Liu*: Aerospace Engineering with Business Minor
- *Allison Hong*: Mechanical Engineering with Aerospace Engineering Minor

## Introduction

Autonomous flight control and guidance in small-scale rocketry requires the simultaneous optimization of aerodynamics, embedded systems, materials science, and control theory. Existing solutions to these problems are confined to proprietary or restricted hardware unavailable for independent research, and no open-source or hobby-scale platform currently integrates active thrust-vector control, a distributed avionics stack, and staged flight capability in a single reproducible system. The WYVERN-E is a full-scale prototype autonomous guided rocket built from commercially available components and hobbyist-level manufacturing techniques, designed to fill this gap and produce openly reproducible hardware, datasets, and design methodology for the broader rocketry community.

The vehicle employs a **two-stage, 84 mm-diameter, additively-manufactured airframe** in which the sustainer carries both the fixed fins and a **closed-loop thrust-vector control (TVC) system** evaluated in two interchangeable forms — a **tri-solenoid actuator** and a **servo-gimbal actuator** — each vectoring the sustainer nozzle ±5° under nested control loops, while four oversized fixed fins provide passive backup stability. An **off-the-shelf flight computer built on a Raspberry Pi 5** executes a multi-input control loop that fuses every onboard sensor. The research program is organized around three experimental campaigns that feed the integrated vehicle: a wind-tunnel study of fin aerofoil profiles and surface treatments, a motor and material-erosion study on a custom thrust stand, and a powered-flight **A/B comparison of the two TVC actuators** (tri-solenoid vs servo). Structural and aerodynamic components are fabricated via fused deposition modeling (FDM) using candidate engineering filaments characterized per Dizon et al. (2018), and fin cross-section profiles are evaluated against low-Reynolds-number aerodynamic theory established by Lissaman (1983) and Mueller and DeLaurier (2003).

To support ground-based aerodynamic characterization alongside flight testing, a custom open-return low-speed wind tunnel based on the Hofferth (2025) AIAA SciTech modular design is constructed in parallel with the vehicle, following tunnel design criteria from Mehta and Bradshaw (1979) and Pope and Harper (1966). Together, the wind tunnel, the motor test stand, computational simulations in OpenRocket and SimFlow, and in-situ powered flight testing form a multi-tier experimental framework through which each research question is addressed across multiple validation methods, with all resulting datasets, design files, and firmware released publicly through NAR upon conclusion of the program.

## Research Questions

### Research Question 1 — Fin Aerofoil Profile and Deflection Aerodynamics

Testing thin symmetric NACA (NACA 0006), moderate symmetric NACA (NACA 0012), double-wedge, and flat-plate fin cross-sections — all printed in basic PLA so that cross-sectional geometry is the only variable — in the Hofferth open-return wind tunnel, the lift coefficient, drag coefficient, and normal-force response of each profile will be measured both straight-on at zero deflection and through commanded deflections applied in 0.5° increments, with the objective of characterizing the deflection-normalized aerodynamic response of each profile to inform fin geometry selection and future thrust-vector control-vane design.

### Research Question 2 — Print Material and Surface Coating Performance for Fins

Holding fin profile constant, fins printed in PC, PETG-CF, ASA Aero, and PLA Basic — each evaluated bare and with a set of candidate surface treatments (automotive filler primer, XTC-3D epoxy smoothing resin, two-part polyurethane clear coat, and VHT high-temperature ceramic paint) — will be compared on printed surface roughness, drag at matched Reynolds number, dimensional fidelity to CAD nominal geometry, and durability under controlled UV exposure, with the objective of identifying the material-and-coating combination that yields the best aerodynamic surface and durability for the vehicle's fins.

### Research Question 3 — Motor Thrust Characterization and Material Erosion as Jetvane Candidates

Using the custom load-cell motor test stand, the thrust-versus-time curve and total impulse of the flight motors will be measured and compared against manufacturer data; an Estes E16-4 exhaust plume will then be directed onto slabs of each candidate material (PC, PETG-CF, ASA Aero, PLA Basic) to quantify mass loss and erosion rate and to assess structural survival, with the objective of determining which materials can withstand direct exhaust-plume exposure as jetvane/TVC-vane candidates and endure the structural stresses of flight. This campaign constitutes the structural and materials aspect of the project.

### Research Question 4 — TVC Actuation A/B: Solenoid vs Servo Control Authority in Powered Flight

Two interchangeable TVC actuators — a tri-solenoid system and a high-torque servo-gimbal system (BPS-style, up-rated ~8× for the G-class thrust) — are flown head-to-head on the same Raspberry Pi 5 airframe over a long (4.7 s) sustainer burn (3 flights each). Stabilization time, commanded-maneuver tracking error, control bandwidth, slew rate, deadband/backlash, and power/mass are characterized for both, with the objective of determining which actuator gives better closed-loop control authority for an amateur TVC rocket at this thrust class.

## Project Goal

The goal of the WYVERN-E project is to design, fabricate, and flight-test the WYVERN-E system, a recoverable full-scale prototype autonomous guided rocket based on an 84 mm two-stage airframe whose sustainer carries the fins and a thrust-vector control system built in two interchangeable forms (solenoid and servo). The system serves as an integrated test platform for evaluating fin aerofoil aerodynamics under deflection, the performance of 3D-printable materials and surface coatings, the erosion and structural survival of those materials under direct motor-exhaust exposure, and an A/B comparison of solenoid vs servo TVC control authority. Testing is conducted using computer-based CFD and FEA simulations, ground-based wind tunnel and motor-stand testing, and in-situ powered flight, with the goal of producing usable datasets and reliable components for the rocketry community.

## Proposed Methodologies

The WYVERN-E program employs a multi-tier experimental framework spanning computational simulation, ground-based wind tunnel testing, ground-based motor and erosion testing, and in-situ powered flight. Each research question is addressed through at least two of these tiers to enable cross-validation of results. All fabrication utilizes hobbyist-accessible manufacturing methods and commercially available components, consistent with the project's open-source objectives.

### Airframe & Materials

All primary structural and aerodynamic components, including the airframe body-tube sections, nose cone, sustainer fin module, interstage coupler, and TVC housing, are fabricated via FDM on a Bambu Lab X1C printer using the factory 0.4 mm nozzle. Print parameters including layer height, infill pattern and density, wall count, print temperature, and part cooling are held constant across all test articles to isolate material and coating as the independent variables for Research Question 2, following the methodology established by Popescu et al. (2018) for FDM parameter control. A standardized parameter profile is developed and frozen prior to the first production run, and all airframe prints reference this profile. The four candidate filaments are PC (polycarbonate) for high-temperature and impact performance, PETG-CF (carbon-fiber-reinforced PETG) for stiffness, ASA Aero for UV and weather stability, and PLA Basic as the accessible baseline control. The selection of carbon-fiber-reinforced filament is motivated by Bhandari et al. (2019), who demonstrated measurable improvements in interlayer tensile strength for short-carbon-fiber-reinforced PETG over unfilled variants; PLA and PETG thermal and mechanical behavior across print conditions is characterized per Hsueh et al. (2021). Components in the motor thermal field — the TVC cradle, gimbal, and motor test stand — are printed in flame-retardant polycarbonate (PC-FR) for its ~140 °C heat-deflection temperature and self-extinguishing behavior.

Four candidate surface treatments are evaluated against a bare-print control for Research Question 2: a sanded automotive filler primer (e.g., Rust-Oleum Automotive Filler Primer) to fill layer lines for aerodynamic smoothness, XTC-3D two-part epoxy smoothing resin (Smooth-On) for layer-line fill and added surface stiffness, a two-part (2K) polyurethane clear coat for a durable hard finish, and VHT Flameproof high-temperature ceramic paint (rated to ~1300 °F / 700 °C) for thermal and erosion resistance relevant to control-vane applications. Dimensional accuracy is verified post-treatment using digital calipers with deviation from CAD nominal geometry recorded per part, surface roughness is characterized using profilometry, and flexural stiffness of each base material is characterized under standardized 3-point bend loading per Dizon et al. (2018), whose mechanical characterization framework for FDM-printed polymers provides the basis for the test protocol used here.

### Fins & Aerofoil Profiles

Four fin cross-section profiles are fabricated for wind tunnel evaluation: a thin symmetric NACA profile (NACA 0006), a moderate symmetric NACA profile (NACA 0012), a double-wedge, and a flat-plate, all printed in basic PLA to isolate cross-sectional geometry. Symmetric NACA section aerodynamic data referenced in Abbott and Von Doenhoff (1959) and the NACA 0012 characterization from NACA TN 2502 provide baseline expected performance at low angles of attack. Each profile is mounted one at a time on a deflection-indexed balance in the wind tunnel and swept both straight-on and through commanded deflections in 0.5° increments, so that the deflection-normalized lift and drag response of each profile is captured directly. Low-Reynolds-number aerodynamic behavior is framed using Lissaman (1983) and Mueller and DeLaurier (2003). Because the WYVERN-E fins are fixed passive-stability surfaces on the sustainer backing up the active TVC, the down-selection objective is the profile that delivers stable behavior and minimum parasitic drag at a target static margin of 1.0–2.0 calibers; fin geometry for the flight vehicle is confirmed through OpenRocket stability simulation using the Barrowman (1967) center-of-pressure method implemented in that tool.

### Motor Test Stand & Jetvane Material Erosion

A custom vertical thrust stand (PC-FR) characterizes the candidate motors: a 29 mm motor cradle transmits axial thrust into a Wishiot bar load cell (HX711 amplifier) read by an Adafruit Metro M4 logging to a microSD breakout, calibrated against an Estes E16-4 reference. The thrust-versus-time curve, peak thrust, and integrated total impulse are extracted for each motor and compared against manufacturer and ThrustCurve.org data, with a minimum of three static fires per motor type to assess repeatability. To address the structural and materials objective of Research Question 3, an E16-4 exhaust plume is then directed at a fixed standoff onto slabs of each candidate print material (PC, PETG-CF, ASA Aero, PLA Basic); pre- and post-exposure mass and profilometry quantify mass-loss and erosion rate, and the slabs are inspected for charring, melting, and structural failure. The results rank the materials for survivability as jetvane/TVC-vane candidates and under the thermal and mechanical stresses of flight, informing both the TVC mechanism and the flight airframe material down-selection. The jetvane material-property baseline draws on the machinable-ceramic suitability framework in the Precision Ceramics (2021) Macor technical data sheet as a high-temperature reference point.

### Flight Computer Systems & Avionics

The flight computer is **completely off-the-shelf**, built on a **Raspberry Pi 5 (4 GB)** with an active cooler and a Camera Module 3, on a COTS sensor harness (no custom PCBs). The sustainer TVC gimbal is driven by **one of two interchangeable actuator systems**: System A — three 12 V pull-solenoids at 120°, each a low-side-MOSFET PWM channel with freewheel diode and current-sense shunt, spring-return to fail-safe neutral; System B — three ~35 kg·cm digital metal-gear servos driven from a PCA9685 PWM expander through gimbal linkages. A remove-before-flight jumper pin arms the computer on the rod (pyro held safe while inserted), and launch is detected by an accelerometer threshold. Sensing: three Bosch **BNO085** 9-DOF units (gimbal, central FC, nose), an ST **LSM6DSO32** ±32 g IMU, an ST **LIS2MDL** magnetometer, a **BMP280** barometer, and a **BME688** gas/temperature/pressure/humidity sensor. All data is logged to **dual microSD** (one video, one sensor log) and retrieved post-flight; the vehicle carries no radio link. An **RRC3+** controls 2nd-stage ignition and dual-deploy recovery.

### Simulations, Firmware, and Modelling

Flight software runs on the Raspberry Pi 5 (Linux) in C/Python. It implements a multi-input control loop that fuses every onboard sensor — the LSM6DSO32 and LIS2MDL feeding a complementary filter (Mahony et al., 2008) cross-checked against the three BNO085 fused quaternions (gimbal, central FC, and nose), with barometric input — to compute attitude error relative to the pre-loaded nominal trajectory and output actuator commands to whichever TVC system is fitted: a 3-coil PWM mixing law for the solenoid system, or proportional gimbal angles for the servo system. Gain values are tuned iteratively using the Ziegler-Nichols (1942) step-response method. OpenRocket is used for pre-flight stability analysis, center-of-pressure and center-of-mass tracking across both motor burns, staging-event modeling, and nominal trajectory prediction per the OpenRocket technical documentation (2023), with simulated outputs compared against the recorded onboard flight data as a cross-validation metric. SimFlow, operating on an OpenFOAM finite-volume solver, is used for steady-state and transient CFD analysis of individual fin profiles and the full vehicle at representative flight Reynolds numbers consistent with the low-Reynolds-number regime defined by Mueller and DeLaurier (2003) and Lissaman (1983); simulations are run at deflection increments corresponding to the wind tunnel test conditions, enabling direct comparison of CFD-predicted lift and drag coefficients against measured tunnel values, with mesh-refinement studies confirming solution convergence. FEA is conducted on fin and airframe cross-sections for each candidate print material using property inputs derived from the 3-point bend and erosion test results.

### Wind Tunnel

The custom open-return wind tunnel is designed per the Hofferth (2025) AIAA SciTech modular configuration and comprises a bell-mouth inlet, a flow-conditioning section with honeycomb and mesh screens, a converging contraction section designed per Bell and Mehta (1988) area-ratio and length criteria, an optically accessible test section, and a diffuser leading to a variable-speed fan unit. Tunnel design also draws on the low-speed tunnel design rules of Mehta and Bradshaw (1979) and the reference design methodology of Pope and Harper (1966). Prior to aerodynamic testing, the tunnel is characterized across its full operating range using a Pitot-static probe traversed across the test-section cross-section at multiple fan-speed settings to map freestream velocity and spatial uniformity, with a uniformity target of less than 2% RMS variation in the core flow region. Blockage corrections are applied to all measured drag coefficients using the Maskell (1963) bluff-body blockage correction method, and Reynolds number similarity ratios between tunnel and flight conditions are computed to identify the Reynolds-matched operating point. Each fin profile, material, and coating test article is mounted one at a time on a deflection-indexed two-axis force balance and recorded at equal angle-of-attack and 0.5° deflection increments from 0° through post-stall, with a minimum of three repeated runs per condition to assess repeatability. Airfoil section data from Selig (2003) and Selig et al. (1989) are used as reference benchmarks against which tunnel-measured coefficients for the NACA profiles are validated prior to cross-profile comparison.

### Flights, Logs, and Data Sharing

All flights are conducted in compliance with NAR (2023) safety code and motor classification standards, with a NAR representative or similarly qualified adult present at each flight session. For Research Question 4, instrumented two-stage flights are conducted on an F-class booster and a long-burn AeroTech G25W sustainer (4.7 s TVC window); the onboard flight logs record the booster-separation tip-off rate, the post-staging attitude-recovery time and overshoot, commanded gimbal angle and per-coil current, achieved attitude, and command-to-response latency through the staging transition and the controlled sustain phase. A firmware arm-gate keyed to the staging state machine inhibits the booster recovery charge until sustainer ignition and separation are confirmed, so that no parachute is ever deployed under thrust. All onboard sensor data is logged to the SD-NAND recorder at the flight-computer sample rate, with an edge microSD backup, and retrieved post-flight for analysis; the vehicle carries no radio downlink. Upon conclusion of the program, all datasets, CAD files, PCB design files, firmware source code, and OpenRocket and SimFlow simulation files are released publicly through NAR and the project repository in support of the WYVERN-E open-source objectives.

## Expected Outcomes

We expect several outcomes from our research and prototyping. We will produce a deflection-resolved aerodynamic dataset showing how thin-NACA, thick-NACA, double-wedge, and flat-plate fin profiles respond straight-on and through 0.5° deflection increments, informing fin and future control-vane geometry. We will identify the optimal print material and surface coating for hobbyist 3D-printed fins by quantifying surface roughness, drag, dimensional fidelity, and durability across PC, PETG-CF, ASA Aero, and PLA Basic with bare, filler-primer, epoxy-smoothed, clear-coated, and high-temperature-ceramic finishes — an area not commonly addressed in rocketry literature that tends to prefer wood or fiberglass construction. We will characterize the flight motors' thrust-versus-time and total impulse on a custom load-cell stand, and rank the candidate materials by their erosion and structural survival under a direct motor-exhaust plume, determining which can serve as jetvanes for future TVC operations and withstand the stresses of flight. Finally, we will produce a head-to-head dataset comparing tri-solenoid versus servo-gimbal TVC control authority on the same Raspberry Pi 5 airframe over a long sustainer burn, identifying which actuator better serves amateur TVC at the G-motor thrust class. All data will be released as publicly available datasets through NAR, with the rocket components developed into reproducible open-source systems.

## References

Abbott, I. H., & Von Doenhoff, A. E. (1959). *Theory of wing sections: Including a summary of airfoil data.* Dover Publications.

Barrowman, J. S. (1967). *The practical calculation of the aerodynamic characteristics of slender finned vehicles* (NASA NTRS accession 20010047838).

Bell, J. H., & Mehta, R. D. (1988). *Contraction design for small low-speed wind tunnels* (NASA CR-182747).

Bhandari, S., Lopez-Anido, R. A., & Gardner, D. J. (2019). Enhancing the interlayer tensile strength of 3D printed short carbon fiber reinforced PETG. *Composites Part B: Engineering, 179,* 107542.

Chacón, J. M., Caminero, M. A., García-Plaza, E., & Núñez, P. J. (2017). Additive manufacturing of PLA structures using fused deposition modelling. *Composite Structures, 182,* 107–116.

Dizon, J. R. C., Espera, A. H., Chen, Q., & Advincula, R. C. (2018). Mechanical characterization of 3D-printed polymers. *Additive Manufacturing, 20,* 44–67.

Hofferth, J. (2025). Modular wind tunnel for STEM education. *AIAA SciTech 2025 Forum.*

Hsueh, M.-H., Lai, C.-J., Liu, K.-Y., Chung, C.-F., Wang, S.-H., Pan, C.-Y., Huang, W.-C., Hsieh, C.-H., & Zeng, Y.-S. (2021). Effects of printing parameters on the thermal and mechanical properties of 3D-printed PLA and PETG. *Polymers, 13*(13), 2092.

Lissaman, P. B. S. (1983). Low-Reynolds-number airfoils. *Annual Review of Fluid Mechanics, 15,* 223–239.

Mahony, R., Hamel, T., & Pflimlin, J.-M. (2008). Nonlinear complementary filters on the special orthogonal group. *IEEE Transactions on Automatic Control, 53*(5), 1203–1218.

Maskell, E. C. (1963). *A theory of the blockage effects on bluff bodies and stalled wings in a closed wind tunnel* (ARC R&M 3400). Aeronautical Research Council.

Mehta, R. D., & Bradshaw, P. (1979). Design rules for small low speed wind tunnels. *Aeronautical Journal, 83*(827), 443–449.

Mueller, T. J., & DeLaurier, J. D. (2003). Aerodynamics of small vehicles. *Annual Review of Fluid Mechanics, 35,* 89–111.

National Advisory Committee for Aeronautics. (1951). *Aerodynamic characteristics of NACA 0012 airfoil section at angles of attack from 0° to 180°* (NACA TN 2502).

National Association of Rocketry. (2023). *NAR safety code and motor classification standards.*

OpenRocket Project. (2023). *OpenRocket technical documentation v23.09.*

Pillay, S., Vaidya, U. K., & Janowski, G. M. (2009). Effects of moisture and UV exposure on liquid molded carbon fabric reinforced nylon 6 composite laminates. *Composites Science and Technology, 69*(6), 839–846.

Popescu, D., Zapciu, A., Amza, C., Baciu, F., & Marinescu, R. (2018). FDM process parameters influence over the mechanical properties of polymer specimens. *Polymer Testing, 69,* 157–166.

Pope, A., & Harper, J. J. (1966). *Low-speed wind tunnel testing.* Wiley.

Precision Ceramics. (2021). *Macor machinable glass ceramic — technical data sheet.*

Raspberry Pi Ltd. (2024). *Raspberry Pi 5 product brief and documentation.* Bosch Sensortec, BNO085 datasheet.

Selig, M. S. (2003). *UIUC airfoil data site.* University of Illinois at Urbana-Champaign.

Selig, M. S., Donovan, J. F., & Fraser, D. B. (1989). *Airfoils at low speeds* (Soartech 8). SoarTech Publications.

Ziegler, J. G., & Nichols, N. B. (1942). Optimum settings for automatic controllers. *Transactions of the ASME, 64,* 759–768.

---

## Past Abstracts

### Swaroop Sahoo — Evaluating the Efficiency, Practicality, and Effectiveness of Emission/Reception-Capable LiDAR and RaDAR Detection Systems in Autonomous Navigation

Autonomous vehicles are swiftly evolving from experimental prototypes to a social norm. Advanced emitter-based sensor technologies, including LiDAR and RaDAR, are at the heart of these developments. This research explored, through an analysis of raw performance, which is best for autonomous navigation systems. With an R2 Smart Car, we conducted extensive testing to ascertain detection capability across various terrains and conditions. We hypothesized that if an autonomous vehicle employs LiDAR sensors rather than RaDAR sensors, it will realize better detection owing to its higher resolution, precision, and finer performance for short-range distances. During our trials, LiDAR consistently outperformed RaDAR in precision and recognition of objects within close and medium ranges; however, RaDAR showed better performance in adverse weather conditions. Despite LiDAR's superior detection performance, several challenges were identified: higher cost, greater energy demands, and limited field of view. The experiment shows that a multi-sensor approach is needed to combine the strengths of both for maximum detection accuracy and system reliability.

### Chris Liu — In-Situ Resource Utilization-Derived Iron Perchlorate Redox Flow Battery for Mars: Electrolyte Characterization and Extreme Cold Performance Validation

Sustained habitation on Mars demands robust energy storage capable of reliable operation under extreme cold. This work introduces an in-situ resource utilization (ISRU) strategy for constructing iron perchlorate redox flow batteries from Martian-available materials. Eutectic freezing points and ionic conductivities of three electrolytes (iron sulfate, iron chloride, iron perchlorate) were characterized; iron perchlorate at 45 wt% displayed a eutectic freezing point of −78 °C, outperforming iron chloride (−55 °C) and iron sulfate (−10 °C). The iron perchlorate system maintained 56% of its room-temperature capacity at −50 °C and remained operational at −70 °C. The results establish that ISRU-derived iron perchlorate flow batteries offer a feasible, cold-resilient solution for reliable energy storage in future Mars surface operations.

### Allison Hong — The Effects of Different Types of Synthetic Retinoids on Bacteria Inhibition: Antibacterial Properties

This experiment aimed to determine the inhibitory properties of Adapalene and Tretinoin on *Escherichia coli* K-12. We hypothesized that the tretinoin group would have a greater inhibitory effect than the adapalene group. Agar petri dishes were swabbed with E. coli and incubated for six days; Adapalene Gel 0.1% and Tretinoin Gel 0.1% were diluted with methyl alcohol and added on day two. The retinoids, especially adapalene, were found to promote bacterial growth rather than inhibit it. All three groups followed a polynomial regression, and each result was evaluated with a t-test, with all data significant. Further research is suggested to better understand the retinoids' effects on bacterial growth and inhibition.

---

*Acknowledgment of Senior Research forms (signed) are appended separately and carry over unchanged from the prior submission.*
