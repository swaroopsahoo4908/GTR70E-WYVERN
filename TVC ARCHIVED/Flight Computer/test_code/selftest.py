#!/usr/bin/env python3
"""GTR70E WYVERN preflight self-test runner.

Connects to the Pico 2 W perfboard (RP2350) over USB serial, power-cycles or resets are NOT performed by this script
(reset the board yourself, or it will simply listen to whatever the board is already printing), and
tabulates the BOOT-state SELFTEST:* lines emitted by build/firmware/wyvern4_tvc.ino's setup()/
setup1(). The table below is generated from a live serial session via host_monitor.py, not printed
unconditionally.

Checks performed by the firmware and reported here (see CONFLICTS.md for the frozen parameter
table these depend on):
  IMU_EXTERNAL BNO085 on the shared I2C bus (STEMMA-QT) inits + GRV report enabled
  IMU_BODY BNO085 on the shared I2C bus inits + IMUPLUS mode enabled
  IMU_MINIMUM both IMUs initialized -- flight-critical minimum
  BARO_BME BME688 on the shared I2C bus (0x76) inits
  SERVO pitch/yaw sweep to the full +-8 deg limit completes without a hang
                 (visually confirm actual nozzle travel on the bench -- see test_code/t3)
  CORE0_READY core 0's own init sequence finished
  BATTERY rail voltage above CRITICAL_CUTOFF_V (see battery.h; reads the buck rail, not raw pack)
  SD microSD (SPI0) mounts and the flight-log file opens for write
  WIFI bench WiFi association, only if WIFI_ENABLED is set in the .ino (SKIP otherwise -- the Pico 2 W perfboard has
                 no radio chip populated, so this stays SKIP in flight configuration)
  RBF Remove-Before-Flight switch sensed pulled (PASS) or still inserted (WAIT) -- not wired to a
                 physical switch on this board rev, see 01_FlightComputer_Spec.md section 3
  LOG_RING core 0 -> core 1 shared-RAM log ring is actually moving (core 1 draining), and
                 zero frames dropped during the boot window

Usage:
    python3 selftest.py [PORT] [--timeout SECONDS]
Exit code 0 only if every check above reported PASS (or SKIP for WIFI) and SELFTEST:DONE:PASS was
seen -- suitable for a CI-style "go/no-go" gate in a bench checklist script.
"""
import sys
import argparse

import host_monitor


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("port", nargs="?", default="/dev/ttyACM0",
                     help="serial port (e.g. /dev/ttyACM0, or /dev/tty.usbmodemXXXX on macOS)")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds to listen (default 20)")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    print("GTR70E WYVERN PREFLIGHT SELF-TEST")
    print("Reset the Pico now if you haven't already -- BOOT self-test runs once at power-up.\n")
    rc = host_monitor.run(args.port, args.timeout, args.baud)
    print("\n>>> PREFLIGHT GO <<<" if rc == 0 else "\n>>> PREFLIGHT NO-GO -- see FAIL/NOT SEEN rows above <<<")
    return rc


if __name__ == "__main__":
    sys.exit(main())
