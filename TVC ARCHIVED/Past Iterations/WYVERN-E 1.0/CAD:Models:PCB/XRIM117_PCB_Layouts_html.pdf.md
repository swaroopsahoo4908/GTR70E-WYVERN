---
source_file: "XRIM117_PCB_Layouts_html.pdf"
source_type: "PDF"
updated_at: 2026-05-26
---
# XRIM117_PCB_Layouts_html

*Extracted from [[XRIM117_PCB_Layouts_html.pdf]]*

---

XRIM-117 WYVERN 70mm PTD                                                         PDR-002 Rev A

PCB Layout Diagrams — CCM · ASAM-1 · ASAM-2 | Skylight Industries LLC | 62mm Circular, 2-Layer FR4, ENIG




    CCM — Central Command Module
    RP2040 · ICM-42688-P · BMP388 · Ebyte E22-900M22S · 3× Pyro MOSFET · 1S 850mAh LiPo · 62mm circular


                                    SMA                                 Ref          Component            Package           Function

                                                                        U1           RP2040               QFN-56            Primary MCU, 133MHz dual M0+

                                                                        U2           W25Q128JVSIQ         SOIC-8            16MB QSPI flash — telemetry
                        FLASH
                                       Ebyte E22                                                                            log
                        16MB         SX1268 915MHz
                                      22dBm LoRa
                                                                        U3           ICM-42688-P          LGA-14            Primary IMU, SPI 32kHz ODR
                                        IMU
                        RP2040         42688                            U4           BMP388               LGA-8             Primary barometer, I2C 200Hz
                        QFN-56
                        133MHz         BMP                              U5           Ebyte E22-           SMD module        LoRa 915MHz, SX1268, 22dBm
                                       388                                           900M22S
                 Q1     3V3
                                             J1 → ASAM-1                U6           TLV62569             SOT-23-5          3.3V 600mA buck for logic
                 Q2                          J2 → ASAM-2
                                                                        Q1–Q3        IRFZ44N ×3           TO-               Pyro MOSFET channels
                                                SWD
                 Q3           XT30 BATARM SW                                                              220/D2PAK

                 CH1 CH2 CH3                                            J1           JST-GH 8-pin         Through-hole      ASAM-1 ribbon connector
                        CCM · 62mm · ENIG                               J2           JST-GH 8-pin         Through-hole      ASAM-2 ribbon connector

                                                                        J3           SMA edge-mount       PCB mount         915MHz antenna pigtail

                                                                        J4           XT30-M               Through-hole      1S 850mAh LiPo input

                                                                        J5           2-pin screw term.    Through-hole      Physical arm switch

                                                                        J6–J8        2-pin screw ×3       Through-hole      Pyro e-match outputs CH1–3

                                                                        SW1          TC2030               SMD 6-pin         SWD debug + UART boot

                                                                        LED1–        Bicolor LED ×3       0805              Pyro continuity (CH1–3)
                                                                        3

                                                                        Passives: 100nF+10μF decoupling on each IC power rail. Antenna keepout: 10mm no-
                                                                        copper around SMA. 100Ω series on crystal lines.



                                                                         SMA connector sits at 12 o'clock board edge. LoRa RF trace from E22 to SMA must
                                                                         be 50Ω controlled impedance (~0.9mm trace width on 1.6mm FR4). Keep 10mm
                                                                         copper-free keepout around antenna pad. Route IMU SPI traces <20mm with
                                                                         matched lengths.


     LoRa / RF    Pyro MOSFET        MCU / logic IC        Connector / power    Sensor




    ASAM-1 — Mid Ring Controller
    STM32F411 · ICM-42688-P · MS5611 · 4× Servo Outputs (Ring 2 mid fins) · MT3608 7.4V boost · 1S 1000mAh LiPo · 62mm circular


                                                                        Ref         Component            Package         Function
                              J1 → CCM ribbon

                                                                        U1          STM32F411CEU6        UFQFPN-48       MCU, Cortex-M4 100MHz FPU

                                                                        U2          ICM-42688-P          LGA-14          Redundant IMU, SPI 32kHz
                  J2   MT3608
                 Fin1 → 7.4V HV L      470 470 470 470
                  N                                                     U3          MS5611               SMD-8           Redundant barometer, SPI 150Hz
                  J3                       IMU                          U4          INA219               SOT-23-8        Servo current monitor (7.4V rail)
                 Fin2     STM32
                  E
                                          42688
                         F411CEU6
                        100MHz M4 MS5611                                U5          TLV62569             SOT-23-5        3.3V 600mA logic buck
                  J4
                 Fin3              BARO
                  S                                                     U6          MT3608               SOT-23-6        Boost: 1S LiPo → 7.4V HV servo rail
                                          INA219
                  J5
                 Fin4                                                   L1          4.7μH inductor       0805            MT3608 boost inductor
                  W     3V3
                                                                        J1          JST-GH 8-pin         Through-        CCM inter-board ribbon (top edge)
                                          SWD                                                            hole
                         XT30 1S BAT

                                                                        J2–J5       JR/Futaba 3-pin ×4   Through-        Servo outputs — Ring 2 fins
                                                                                                         hole            N/E/S/W
                                                                                       hole            N/E/S/W
                 ASAM-1 · 62mm · ENIG
                                                     J6        XT30-M                  Through-        1S 1000mAh LiPo input
                                                                                       hole

                                                     C1–C4     470μF electrolytic      Radial          Bulk capacitance on 7.4V servo rail
                                                               ×4                      6.3mm

                                                     C5–       100nF ceramic ×16       0402            Decoupling on all IC power pins
                                                     C20

                                                     R1–R4     10kΩ ×4                 0402            I2C pull-ups SDA/SCL

                                                     SW1       TC2030                  SMD 6-pin       SWD programming + UART
                                                                                                       bootloader

                                                     PWM: TIM1_CH1–CH4 on PA8–PA11. Servo connector order clockwise from North: J2/J3/J4/J5.
                                                     7.4V HV rail separate from 3.3V logic.



                                                      MT3608 boost converter requires careful layout: short traces from inductor to IC,
                                                      large pour on output side, output caps close to servo connector ground pins. 7.4V
                                                      servo rail is isolated from 3.3V logic rail — ground planes share only at one star
                                                      point near the input connector.




ASAM-2 — TVC + Sustainer Controller
STM32F411 · ICM-42688-P · MS5611 · 2× TVC Servo Outputs (jetavane pitch/yaw) · Sustainer Relay · MT3608 7.4V · 1S 1200mAh LiPo ·
62mm circular


                         J1 → CCM ribbon
                                                     Ref     Component              Package        Function

                                                     U1      STM32F411CEU6          UFQFPN-48      MCU, Cortex-M4 100MHz, 2× PWM TIM
                                                                                                   outputs
                  MT3608                             U2      ICM-42688-P            LGA-14         Redundant IMU, SPI 32kHz
                 → 7.4V HV L      470 470 470


                                                     U3      MS5611                 SMD-8          Redundant barometer, SPI 150Hz
                                IMU
            J2        STM32    42688
           TVC      F411CEU6                         U4      INA219                 SOT-23-8       Servo current monitor (7.4V rail)
           PCH
                     2× PWM MS5611
                   TVC + relay BARO                  U5      TLV62569               SOT-23-5       3.3V 600mA logic buck
            J3
           TVC
           YAW                    INA219PC817
                                                     U6      MT3608                 SOT-23-6       Boost: 1S LiPo → 7.4V HV servo rail
                  TPS5430                  IRFZ44
                   5V 3A
                                           SUSTAIN   U7      TPS5430                TO-263-7       5V 3A buck (extra MCU headroom)
                                            RELAY
                   3V3
                                SWD
                                           E-MATCH
                   XT30 1S 1.2Ah
                                           REED SW
                                                     U8      PC817                  DIP-4          Sustainer ignition relay isolation
                                                             optocoupler

                 ASAM-2 · 62mm · ENIG                Q1      IRFZ44N                TO-            Sustainer e-match MOSFET relay
                                                                                    220/D2PAK

                                                     J1      JST-GH 8-pin           Through-       CCM inter-board ribbon (top edge)
                                                                                    hole

                                                     J2–J3   JR/Futaba 3-pin        Through-       TVC Pitch servo (J2) and TVC Yaw servo
                                                             ×2                     hole           (J3)

                                                     J4      XT30-M                 Through-       1S 1200mAh LiPo input
                                                                                    hole

                                                     J5      2-pin screw term.      Through-       Sustainer e-match output
                                                                                    hole

                                                     J6      2-pin header           Through-       Booster eject reed switch
                                                                                    hole

                                                     C1–     470μF electrolytic     Radial 8mm     Bulk cap on 7.4V rail (2 TVC servos)
                                                     C3      ×3

                                                     L1      4.7μH inductor         0805           MT3608 boost inductor

                                                     SW1     TC2030                 SMD 6-pin      SWD debug + UART boot

                                                     TVC servos on TIM2_CH1 (PA0) and TIM2_CH2 (PA1). Aft fins are passive (no PWM channels
                                                     required). Sustainer relay fires on UART command from CCM decoded by STM32 → PC817 →
                                                     IRFZ44N → e-match.



                                                      With passive aft fins, ASAM-2's servo load drops dramatically — only the 2 TVC
                                                      servos remain on the 7.4V rail. Peak simultaneous stall is 2× 1.5A = 3A
                                                      instantaneous. Three 470μF bulk capacitors are more than adequate to prevent
                                                      voltage sag during TVC corrections. Place capacitors within 5mm of TVC connector
                                                      ground pins. IRFZ44N gate must still be driven via PC817 optocoupler for galvanic
                                                      isolation from CCM logic ground.
       Sustainer relay   TVC servo outputs   Boost converter   Power connector




XRIM-117 WYVERN PDR-002 Rev A — PCB Layout Reference | Skylight Industries LLC | CONFIDENTIAL | All boards: 62mm circular, 2-layer FR4 1.6mm, ENIG, JLCPCB
fabrication