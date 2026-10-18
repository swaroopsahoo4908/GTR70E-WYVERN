---
source_file: "WYVERN-E.pdf"
source_type: "PDF"
updated_at: 2026-05-26
---
# WYVERN-E

*Extracted from [[WYVERN-E.pdf]]*

---

WYVERN-E: Engineering Design and Experimental Validation of Active Flight Control,

       Materials, Aerodynamic Optimization, and Wind Tunnel Evaluation in a

                Subscale-Demonstrator Autonomous Guided Rocket


                     Allison Hong, Chris Liu, Swaroop K. Sahoo


                                 April 20th, 2026
WYVERN-E Flight Demonstrator Project                                                          1


Table of Contents
Table of Contents​                                                                              1
Student Information​                                                                            2
Introduction​                                                                                   2
Research Questions​                                                                             3
        Research Question 1 - TVC vs. ACFs for Efficient Control Authority​                     3
        Research Question 2 - Structural Performance in 3D Printable Materials​                 3
        Research Question 3 - Aerofoil Profile Efficiency for Subsonic Control​                 3
        Research Question 4 - Wind Tunnel Calibration with In-Situ Performance​                 3
        Research Question 5 - Accuracy of Flight Control Loop Architectures​                    4
Project Goal​                                                                                   4
Proposed Methodologies​                                                                         4
Expected Outcomes​                                                                              8
References​                                                                                     9
Abstracts​                                                                                    13
    Swaroop Sahoo​                                                                            13
        Evaluating the Efficiency, Practicality, and Effectiveness of Emission/Reception-Capable
        LiDAR and RaDAR Detection Systems in Autonomous Navigation​                           13
    Chris Liu​                                                                                14
        In-Situ resource utilization-derived iron perchlorate redox flow battery for Mars:
        electrolyte characterization and extreme cold performance validation​                 14
    Allison Hong​                                                                             15
        The Effects of Different Types of Synthetic Retinoids on Bacteria Inhibition:
        Antibacterial Properties​                                                             15
WYVERN-E Flight Demonstrator Project                                                             2


Student Information
Student Names: Swaroop Sahoo, Chris Liu, Allison Hong

Project Title: WYVERN-E: Engineering Design and Experimental Validation of Active Flight
Control, Materials, Aerodynamic Optimization, and Wind Tunnel Evaluation in a
Subscale-Demonstrator Autonomous Guided Rocket

Research Pathway: Engineering/Innovation Design

Intended Majors:
   -​ Swaroop Sahoo: Electrical Engineering with Aerospace Engineering Minor
   -​ Chris Liu: Aerospace Engineering with Business Minor
   -​ Allison Hong: Mechanical Engineering with Aerospace Engineering Minor


Introduction
         Active flight control and system guidance in small-scale rocketry requires the
simultaneous optimization of aerodynamics, embedded systems, materials science, and control
theory. Existing solutions to these problems are confined to proprietary or restricted hardware
unavailable for independent research, and no open-source or hobby-scale platform currently
integrates dual-mode active control, a distributed avionics stack, and vertical-to-horizontal flight
transition capability in a single system. The WYVERN-E is a full-scale prototype autonomous
guided rocket built from commercially available components and hobbyist-level manufacturing
techniques, designed to fill this gap and produce openly reproducible hardware, datasets, and
design methodology for the broader rocketry community. The vehicle employs a hybrid control
architecture combining four actively-actuated canard fins (ACFs) and a twin-vane ceramic
jetvane thrust-vector control (TVC) system, evaluated across a range of actuator configurations
and flight regimes. A distributed three-board avionics stack executes a multi-input PID control
loop in C, with attitude estimation running on IMU sensor data. Structural and aerodynamic
components are fabricated via FDM using candidate engineering filaments characterized per
Dizon et al. (2018), and fin cross-section profiles are selected and evaluated against
low-Reynolds-number aerodynamic theory established by Lissaman (1983) and Mueller and
DeLaurier (2003). To support ground-based aerodynamic characterization alongside flight
testing, a custom open-return low-speed wind tunnel based on the Hofferth (2025) AIAA
SciTech modular design is constructed in parallel with the vehicle, following tunnel design
criteria from Mehta and Bradshaw (1979) and Pope and Harper (1966). Together, the wind
tunnel, computational simulations in OpenRocket and SimFlow, and in-situ powered flight
testing form a three-tier experimental framework through which each research question is
addressed across multiple validation methods, with all resulting datasets, design files, and
firmware released publicly through NAR upon conclusion of the program.
WYVERN-E Flight Demonstrator Project                                                           3


Research Questions
Research Question 1 - TVC vs. ACFs for Efficient Control Authority
        Substituting ceramic jetavane thrust-vector control for independently servo-actuated
canard fins as the primary attitude actuator, evaluated across a range of airspeeds in both wind
tunnel and powered flight conditions, will produce measurable differences in attitude correction
gain per degree of actuator input, latency, and achievable pitch and yaw rate, with the objective
of determining which actuator type provides greater control authority and whether a crossover
point exists between the two systems.


Research Question 2 - Structural Performance in 3D Printable Materials
​       Holding all FDM print parameters constant across PETG, PETG-CF with 20% carbon
fiber reinforcement, PLA Aero, and ASA Aero, this study will characterize and compare each
material's flexural stiffness under standardized 3-point bend loading, dimensional deviation from
CAD nominal geometry, printed surface roughness, and rate of physical and visual degradation
following controlled UV exposure, with the objective of identifying the most capable filament
for the airframe and fin fabrication.


Research Question 3 - Aerofoil Profile Efficiency for Subsonic Control
​       Testing thin symmetric NACA, moderate symmetric NACA, double-wedge, and
flat-plate fin cross-sections across incrementally increasing angles of attack in subsonic wind
tunnel flow, lift coefficient, drag coefficient, lift-to-drag ratio, and stall onset angle will be
compared across profiles to determine which geometry produces the most favorable aerodynamic
performance for a fin operating under active deflection.


Research Question 4 - Wind Tunnel Calibration with In-Situ Performance
​       Incrementally adjusting fan speed and configuration across a range of test section
velocity and static pressure settings in the custom open-return low-speed wind tunnel, the
Reynolds number similarity ratio, blockage-corrected drag coefficient, and cross-sectional flow
uniformity will be evaluated at each condition to identify the combination of flow velocity and
static pressure that most closely replicates predicted loading on the vehicle during flight.


Research Question 5 - Accuracy of Flight Control Loop Architectures
        Operating proportional-only, proportional-integral, and full proportional integral
derivative flight computer control loop configurations with gain values tuned iteratively across a
minimum number of repeated flight iterations per configuration, percent deviation from the
nominal pre-plotted flight trajectory, lateral displacement from the intended recovery point at
parachute deployment, and peak attitude error during the powered flight phase will be quantified
and compared to determine which loop architecture produces the greatest trajectory accuracy.
WYVERN-E Flight Demonstrator Project                                                             4


Project Goal
        The goal of the WYVERN-E project is to design, fabricate, and flight-test the
WYVERN-E system, a recoverable full-scale prototype autonomous guided rocket based on a
standard 70mm airframe diameter. The system serves as an integrated test platform for
evaluating methods of actively powered flight control, performance of hobbyist and
industry-grade 3D printable materials, the quantifiable differences in fin aerofoil geometries, the
translation of the constructed test wind tunnel simulations to real world flight data, and the
differences between different levels of flight computer control loop architecture. Testing will be
conducted utilizing computer-based CFD and FEA simulations, ground-based wind tunnel
testing, and in-situ powered flight, with the goal to produce usable datasets and reliable
components for use in the the rocketry community.


Proposed Methodologies
        The WYVERN-E program employs a three-tier experimental framework spanning
computational simulation, ground-based wind tunnel testing, and in-situ powered flight testing.
Each research question is addressed through at least two of these tiers to enable cross-validation
of results. All fabrication utilizes hobbyist-accessible manufacturing methods and commercially
available components, consistent with the project's open-source objectives.

Airframe & Materials
         All primary structural and aerodynamic components, including the airframe body tube,
nose cone, mid-ring fin module, and TVC housing, are fabricated via FDM on a Bambu Lab
X1C printer using the factory 0.4 mm brass nozzle. Print parameters including layer height, infill
pattern and density, wall count, print temperature, and part cooling are held constant across all
test articles to isolate material as the independent variable for Research Question 2, following the
methodology established by Popescu et al. (2018) for FDM parameter control. A standardized
parameter profile is developed and frozen prior to the first production run, and all airframe prints
reference this profile. The four candidate filaments are PETG as a baseline control, PETG-CF
with 20% chopped carbon fiber reinforcement, PLA Aero, and ASA Aero. The selection of
PETG-CF is motivated by Bhandari et al. (2019), who demonstrated measurable improvements
in interlayer tensile strength for short carbon fiber reinforced PETG over unfilled variants. PLA
and PETG thermal and mechanical behavior across print conditions is characterized per Hsueh et
al. (2021). Dimensional accuracy is verified post-print using digital calipers with deviation from
CAD nominal geometry recorded per part, and surface roughness is characterized using
profilometry prior to any post-processing. Flexural stiffness of each material is characterized
under standardized 3-point bend loading per Dizon et al. (2018), whose mechanical
characterization framework for FDM-printed polymers provides the basis for the test protocol
used here.
WYVERN-E Flight Demonstrator Project                                                            5


Fins & Aerofoil Profiles




*Fin Profiles shown above as downward, then right view.

        Four fin cross-section profiles are fabricated for wind tunnel evaluation: a thin symmetric
NACA profile (NACA 0006), a moderate symmetric NACA profile (NACA 0012), a
double-wedge, and a flat-plate. Symmetric NACA section aerodynamic data referenced in
Abbott and Von Doenhoff (1959) and the NACA 0012 characterization from NACA TN 2502
provide baseline expected performance for the NACA profiles at low angles of attack. All
profiles are printed to identical planform dimensions so that only cross-sectional geometry varies
between test articles. Low-Reynolds-number aerodynamic behavior of these profile types is
framed using Lissaman (1983) and Mueller and DeLaurier (2003), both of which establish that
profile geometry effects on lift and drag are particularly pronounced in the subsonic,
low-Reynolds-number regime characteristic of the WYVERN-E flight envelope. Canard
geometry for the flight vehicle is selected based on wind tunnel results and confirmed through
OpenRocket stability simulation using the Barrowman (1967) center-of-pressure method
implemented in that tool.

Flight Computer Systems & Avionics
        The three-board avionics stack is designed in EasyEDA with trace and via placement
handled by the Quilter autorouter, then fabricated boards are manufactured through JLCPCB.
The Central Command Module runs on an RP2040 and hosts the primary flight computer
firmware. ASAM-1, built around an STM32F411, drives the four KST X08 servos controlling
the mid-ring actively controlled fin module, while ASAM-2 uses the same processor to drive
three servos controlling the dual ceramic jetvane TVC assembly. The ceramic jetvane material
selection follows the thermal and mechanical property specifications outlined in the Precision
Ceramics (2021) Macor technical data sheet, which establishes the suitability of machinable
glass ceramic for sustained exposure to solid motor exhaust plumes. Jetvane TVC system design
and characterization draws on Murty and Chakraborty (2015) for numerical performance
WYVERN-E Flight Demonstrator Project                                                           6

expectations and Liu and Hui (2024) for implementation approaches in micro-scale solid motor
TVC systems. Sensor inputs include an ICM-42688-P IMU and BMP388 barometer on the
CCM. A Mahony complementary filter (Mahony et al., 2008) runs on IMU data to produce
stable attitude quaternion estimates for the control loop input. A LoRa 915 MHz link via the
Ebyte E22-900M22S module provides bidirectional telemetry to a laptop ground control station
throughout powered flight.

Simulations, Firmware, and Modelling
        All flight computer firmware is written in C and developed within the PlatformIO
extension for Visual Studio Code, targeting the RP2040 and STM32F411 using their respective
PlatformIO frameworks. The firmware implements a multi-input PID control loop that reads
IMU attitude quaternion estimates, computes attitude error relative to the pre-loaded nominal
trajectory, and outputs servo commands to the ACF and TVC actuators. Three loop
configurations are evaluated for Research Question 5: proportional-only, proportional-integral,
and full proportional-integral-derivative. Gain values for each configuration are tuned iteratively
across repeated flight tests using the Ziegler-Nichols (1942) step-response tuning method. TVC
and ACF control architecture design draws on the low-cost launcher guidance framework
described by Gordillo et al. (2023) and on NASA TN D-4971 (1968) for fundamental TVC
authority and control allocation requirements in solid-propellant systems. OpenRocket is used for
pre-flight stability analysis, center-of-pressure and center-of-mass tracking across motor burn,
and nominal trajectory prediction per the OpenRocket technical documentation (2023), with
simulated outputs compared against flight telemetry as a cross-validation metric.




*OpenRocket Model with Stability and Approximate Dimensions

        SimFlow, operating on an OpenFOAM finite volume solver, is used for steady-state and
transient CFD analysis of individual fin profiles and the full vehicle at representative flight
Reynolds numbers consistent with the low-Reynolds-number regime defined by Mueller and
DeLaurier (2003) and Lissaman (1983). Simulations are run at incrementally increasing angles
of attack corresponding to wind tunnel test conditions, enabling direct comparison of
CFD-predicted lift and drag coefficients against measured tunnel values. Mesh refinement
WYVERN-E Flight Demonstrator Project                                                               7

studies are conducted to confirm solution convergence. FEA is conducted on fin and airframe
cross-sections for each candidate print material using property inputs derived from the 3-point
bend test results, with loading cases corresponding to peak aerodynamic and thrust loads
predicted by OpenRocket.

Wind Tunnel




*Initial 3D Model of the low-speed open-return wind tunnel system

        The custom open-return wind tunnel is designed per the Hofferth (2025) AIAA SciTech
modular configuration and comprises a bell-mouth inlet, a flow-conditioning section with
honeycomb and mesh screens, a converging contraction section designed per Bell and Mehta
(1988) area ratio and length criteria, an optically accessible test section, and a diffuser leading to
a variable-speed fan unit. Tunnel design also draws on the low-speed tunnel design rules of
Mehta and Bradshaw (1979) and the reference design methodology of Pope and Harper (1966).
Prior to aerodynamic testing, the tunnel is characterized across its full operating range using a
Pitot-static probe traversed across the test section cross-section at multiple fan speed settings to
map freestream velocity and spatial uniformity, with a uniformity target of less than 2% RMS
variation in the core flow region. Blockage corrections are applied to all measured drag
coefficients using the Maskell (1963) bluff-body blockage correction method. Reynolds number
similarity ratios between tunnel conditions and powered-ascent flight conditions are computed to
identify the fan operating point at which tunnel aerodynamic loading on the scaled rocket model
most closely replicates predicted loading on the full-scale vehicle during powered ascent.

         Each fin profile test article is mounted on a two-axis force balance string within the test
section and lift and drag forces are recorded at equal angle-of-attack increments from 0° through
post-stall at the calibrated Reynolds-matched condition. Lift coefficient, drag coefficient,
lift-to-drag ratio, and stall onset angle are extracted for each profile, with a minimum of three
repeated runs per angle per profile conducted to assess measurement repeatability. Mean values
from repeated runs are used for all cross-profile comparisons. The complete mid-ring ACF
module is tested at representative cruise airspeeds with servo-commanded deflection inputs
applied in 2° increments to characterize deflection-normalized lift increment as a function of
airspeed, providing the ground-based component of the TVC versus ACF control authority
WYVERN-E Flight Demonstrator Project                                                           8

comparison addressed in Research Question 1. Airfoil section data from Selig (2003) and Selig
et al. (1989) are used as reference benchmarks against which tunnel-measured coefficients for
the NACA profiles are validated prior to cross-profile comparison.

Flights, Logs, and Data Sharing
        All flights are conducted in compliance with NAR (2023) safety code and motor
classification standards, with a NAR representative or similarly qualified adult present at each
flight session. Comparative flights for Research Question 1 are conducted with the control loop
configured to isolate each actuator type: one series uses only the ACF system as the primary
attitude actuator and a separate series uses only the TVC ceramic jetvane system. Telemetry logs
record actuator command angle, achieved attitude, command-to-response latency, and peak pitch
and yaw rates per degree of actuator input across the airspeed range sampled during powered
ascent. The crossover airspeed at which one actuator type produces greater control authority gain
than the other is identified by comparing these metrics between the two actuator series across the
sampled airspeed range. BPS.space TVC design references are used to benchmark expected
jetvane authority against prior hobby-scale implementations. For Research Question 5, a
minimum number of flight repetitions are completed for each of the three loop configurations,
and post-flight telemetry is analyzed for percent deviation from the nominal trajectory, lateral
displacement from the intended recovery point at parachute deployment, and peak attitude error
during the powered flight phase.

        All onboard sensor data is logged at the CCM sample rate and simultaneously
downlinked via the LoRa ground station link, with onboard and downlinked logs cross-checked
post-flight for completeness and consistency. Upon conclusion of the program, all datasets, CAD
files, PCB design files, firmware source code, and OpenRocket and SimFlow simulation files are
released publicly through NAR and the project repository in support of the WYVERN-E
open-source objectives.
WYVERN-E Flight Demonstrator Project                                                             9


Expected Outcomes




*OpenRocket Render of the WYVERN-E in Flight

        We expect to see a few possible outcomes from our research and prototyping journey. We
will be able to see the crossover airspeed for which canard fins outperform internal jetvane TVC
for control authority and which one provides greater control gain to inform future design
decisions, including those for the unexplored transition from vertical to horizontal flight. We will
also be able to identify the optimal material for hobbyist manufacturing utilizing 3D printing for
rapid prototyping and defining which has the best stiffness, print quality, and overall durability,
something not as commonly addressed in rocketry literature which tends to prefer wood or
fiberglass construction. In addition we are looking into the aerofoil profiles and will be able to
experimentally determine which of them produces the most attitude control in an actively
deflected configuration at low Reynolds numbers, with recorded wind tunnel and simulation data
being released as an open-source dataset. The development of the WYVERN-E testing wind
tunnel will give the rocketry community a cost effective and open-source option for
ground-based simulation, powered ascent simulation, and live testing of aerodynamics and
control theory. It will also further expand on that control theory by evaluating the complexity of
control and the performance regimens that can be achieved with different levels of
microprocessor and loop complexity. We hope to be able to release all data as publicly available
datasheets through NAR and develop the rocket components into either fledged out products or
reproducible systems; still committing to full open-source designs and data sharing.
WYVERN-E Flight Demonstrator Project                                                           10

                                           References


Abbott, I. H., & Von Doenhoff, A. E. (1959). Theory of wing sections: Including a summary of

       airfoil data. Dover Publications. https://store.doverpublications.com/0486605868.html

Barrowman, J. S. (1967). The practical calculation of the aerodynamic characteristics of slender

       finned vehicles (NASA NTRS accession 20010047838).

       https://ntrs.nasa.gov/citations/20010047838

Barrowman, J. S. (1967). The theoretical prediction of the center of pressure. Apogee Rockets.

       https://www.apogeerockets.com/downloads/barrowman_report.pdf

Bell, J. H., & Mehta, R. D. (1988). Contraction design for small low-speed wind tunnels (NASA

       CR-182747).

       https://ntrs.nasa.gov/api/citations/19880012661/downloads/19880012661.pdf

Bhandari, S., Lopez-Anido, R. A., & Gardner, D. J. (2019). Enhancing the interlayer tensile

       strength of 3D printed short carbon fiber reinforced PETG. Composites Part B:

       Engineering, 179, 107542. https://doi.org/10.1016/j.compositesb.2019.107542

BPS.space. (n.d.). Thrust vector control. BPS.space. Retrieved April 18, 2026, from

       https://bps.space/products/thrust-vector-control

Chacón, J. M., Caminero, M. A., García-Plaza, E., & Núñez, P. J. (2017). Additive

       manufacturing of PLA structures using fused deposition modelling. Composite

       Structures, 182, 107–116. https://doi.org/10.1016/j.compstruct.2017.09.004

Dizon, J. R. C., Espera, A. H., Chen, Q., & Advincula, R. C. (2018). Mechanical characterization

       of 3D-printed polymers. Additive Manufacturing, 20, 44–67.

       https://doi.org/10.1016/j.addma.2017.12.002
WYVERN-E Flight Demonstrator Project                                                             11

Hofferth, J. (2025). Modular wind tunnel for STEM education. AIAA SciTech 2025 Forum.

       https://doi.org/10.2514/6.2025-2630

Hsueh, M.-H., Lai, C.-J., Liu, K.-Y., Chung, C.-F., Wang, S.-H., Pan, C.-Y., Huang, W.-C.,

       Hsieh, C.-H., & Zeng, Y.-S. (2021). Effects of printing parameters on the thermal and

       mechanical properties of 3D-printed PLA and PETG. Polymers, 13(13), 2092.

       https://doi.org/10.3390/polym13132092

Lissaman, P. B. S. (1983). Low-Reynolds-number airfoils. Annual Review of Fluid Mechanics,

       15, 223–239.

       https://bpb-us-w1.wpmucdn.com/sites.usc.edu/dist/4/81/files/2023/05/lissaman-arfm-198

       3.pdf

Liu, Y., & Hui, W. (2024). Implementation and verification of a micro-jet-vane system of a solid

       rocket motor for a micro-nano satellite. Aerospace, 11(5), 367.

       https://www.mdpi.com/2226-4310/11/5/367

Mahony, R., Hamel, T., & Pflimlin, J.-M. (2008). Nonlinear complementary filters on the special

       orthogonal group. IEEE Transactions on Automatic Control, 53(5), 1203–1218.

       https://hal.science/hal-00488376v1/document

Maskell, E. C. (1963). A theory of the blockage effects on bluff bodies and stalled wings in a

       closed wind tunnel (ARC R&M 3400). Aeronautical Research Council.

       https://reports.aerade.cranfield.ac.uk/handle/1826.2/3452

Mehta, R. D., & Bradshaw, P. (1979). Design rules for small low speed wind tunnels.

       Aeronautical Journal, 83(827), 443–449. https://doi.org/10.1017/S0001924000031985

Mueller, T. J., & DeLaurier, J. D. (2003). Aerodynamics of small vehicles. Annual Review of

       Fluid Mechanics, 35, 89–111. https://doi.org/10.1146/annurev.fluid.35.101101.161102
WYVERN-E Flight Demonstrator Project                                                              12

Murty, M. S. R., & Chakraborty, D. (2015). Numerical characterisation of jet-vane based thrust

       vector control systems. Defence Science Journal, 65(4), 263–270.

       https://www.researchgate.net/publication/283661759_Numerical_Characterisation_of_Jet

       -Vane_based_Thrust_Vector_Control_Systems

National Advisory Committee for Aeronautics. (1951). Aerodynamic characteristics of NACA

       0012 airfoil section at angles of attack from 0° to 180° (NACA TN 2502).

       https://ntrs.nasa.gov/citations/19930082895

National Association of Rocketry. (2023). NAR safety code and motor classification standards.

       https://www.nar.org/safety-information/

NASA. (1968). Thrust-vector control requirements for solid-propellant launch vehicles (NASA

       TN D-4971).

       https://ntrs.nasa.gov/api/citations/19680019218/downloads/19680019218.pdf

OpenRocket Project. (2023). OpenRocket technical documentation v23.09.

       https://openrocket.info/documentation.html

Pérez Gordillo, A., Simplício, P., Iannelli, A., & Marcos, A. (2023). Thrust vector control and

       state estimation architecture for low-cost small-scale launchers. arXiv.

       https://arxiv.org/pdf/2303.16983

Pillay, S., Vaidya, U. K., & Janowski, G. M. (2009). Effects of moisture and UV exposure on

       liquid molded carbon fabric reinforced nylon 6 composite laminates. Composites Science

       and Technology, 69(6), 839–846. https://doi.org/10.1016/j.compscitech.2008.11.012

Popescu, D., Zapciu, A., Amza, C., Baciu, F., & Marinescu, R. (2018). FDM process parameters

       influence over the mechanical properties of polymer specimens. Polymer Testing, 69,

       157–166. https://doi.org/10.1016/j.polymertesting.2018.05.020
WYVERN-E Flight Demonstrator Project                                                          13

Pope, A., & Harper, J. J. (1966). Low-speed wind tunnel testing. Wiley.

       https://archive.org/details/lowspeedwindtunn0000pope

Precision Ceramics. (2021). Macor machinable glass ceramic — technical data sheet.

       https://precision-ceramics.com/wp-content/uploads/2021/06/Macor_Technical_Data_She

       et.pdf

Sahoo, S. (2026, April 11). (Skylight Industries, Ed.). WYVERN PTD Portal; Skylight

       Industries. https://wyvern-e.base44.app/

Selig, M. S. (2003). UIUC airfoil data site. University of Illinois at Urbana-Champaign.

https://m-selig.ae.illinois.edu/ads.html

Selig, M. S., Donovan, J. F., & Fraser, D. B. (1989). Airfoils at low speeds (Soartech 8).

       SoarTech Publications.

       https://m-selig.ae.illinois.edu/ads/afplots/airfoils_at_low_speeds.pdf

Ziegler, J. G., & Nichols, N. B. (1942). Optimum settings for automatic controllers. Transactions

       of the ASME, 64, 759–768.

       https://davidr.no/iiav3017/papers/Ziegler_Nichols_%201942.pdf
WYVERN-E Flight Demonstrator Project                                                              14


Past Abstracts
Swaroop Sahoo
Evaluating the Efficiency, Practicality, and Effectiveness of Emission/Reception-Capable
LiDAR and RaDAR Detection Systems in Autonomous Navigation

       Autonomous vehicles are swiftly evolving from experimental prototypes to a social norm.
Advanced emitter-based sensor technologies, including LiDAR and RaDAR, are at the heart of
these developments. This research has explored, through an analysis of raw performance, which
is best for autonomous navigation systems. With an R2 Smart Car, we had extensive testing with
the setup to ascertain detection capability across various terrains and conditions. We
hypothesized that if an autonomous vehicle employs LiDAR sensors rather than RaDAR sensors,
it will realize better detection owing to its higher resolution, precision, and finer performance for
short-range distances. During our trials, LiDAR always outperformed RaDAR concerning
precision and the recognition of objects within close and medium ranges. However, RaDAR
showed better performance in adverse weather conditions, proving that it is more resistant to
environmental stressors. Despite LiDAR's superior detection performance, several challenges
were identified: higher cost, greater energy demands, and limited field of view. RaDAR, though
less effective in performance, claims advantages regarding cost-efficiency, weather robustness,
and lower battery requirements. These considerations become critical in balancing efficiency
against function while designing a self-driving vehicle. This experiment shows that such a
multi-sensor approach is needed to put together the strengths of LiDAR and RaDAR to attain
maximum detection accuracy and system reliability. Such integration will be imperative for
making robust, cost-effective autonomous systems that are capable of navigating diverse
real-world conditions and thereby fostering the feasibility and safety of autonomous vehicles in
mainstream society.
WYVERN-E Flight Demonstrator Project                                                                  15


Chris Liu
In-Situ resource utilization-derived iron perchlorate redox flow battery for Mars:
electrolyte characterization and extreme cold performance validation

       Sustained habitation on Mars demands robust energy storage systems capable of reliable
operation under extreme cold, especially during night and dust storm periods that render
conventional lithium-ion batteries ineffective. This work introduces an in-situ resource utilization
(ISRU) strategy for constructing iron perchlorate redox flow batteries, fully leveraging
Martian-available materials to achieve extreme cold resilience. Eutectic freezing points and ionic
conductivities of three Martian-available electrolytes (iron sulfate, iron chloride, and iron
perchlorate) were systematically characterized. Iron perchlorate aqueous solution at 45 wt%
displayed a eutectic freezing point of −78 °C, outperforming iron chloride (−55 °C) and iron
sulfate (−10 °C). Laboratory-scale single cells were developed via computer-aided design and
3D printing, then tested under simulated Martian low-temperature conditions. The iron
perchlorate system maintained 56% of its room-temperature capacity at −50 °C and remained
operational at −70 °C, while iron chloride cells retained only 25% at −50 °C and lost
functionality at lower temperatures. Electrochemical impedance measurements revealed that,
although electrolyte resistance increases at lower temperature, charge transfer resistance becomes
the dominant limiting factor under extreme cold. The results establish that ISRU-derived iron
perchlorate flow batteries offer a feasible, cold-resilient solution for reliable energy storage in
future Mars surface operations and settlement, with further performance gains likely through
advanced perchlorate brine formulation.
WYVERN-E Flight Demonstrator Project                                                             16


Allison Hong
The Effects of Different Types of Synthetic Retinoids on Bacteria Inhibition: Antibacterial
Properties
       Retinoids are a group of compounds including naturally occurring and synthetic vitamin
A metabolites and analogs. The two most common synthetic vitamin derivatives are Tretinoin
and Adapelene. This experiment aims to determine the inhibitory properties of Adapalene and
Tretinoin on Escherichia Coli. K-12. We hypothesized that the tretinoin group would have a
greater inhibitory effect than the adapalene group. We created agar petri dishes and swabbed E.
coli. The dishes were incubated for six days in total. Adapalene Gel 0.1% and Tretinoin Gel
0.1% were measured and diluted with Methyl Alcohol. The solutions were added on day two of
incubation. The bacterial growth was counted after the incubation period for the number of
colonies formed on each dish. The retinoids, especially adapalene, were found to promote the
growth of bacteria instead of inhibiting its growth. The data of all three groups represent a
polynomial regression, with adapalene and tretinoin exhibiting an exponential pattern and the
control group exhibiting a logarithmic pattern. Each result was evaluated with the statistical
analysis of a t-test, and all data was significant and not random. Further research is suggested to
better understand the retinoids’ effects on bacterial growth and inhibition.