#!/usr/bin/env python3
"""Scan I2C1 and each TCA9548A channel; confirm every WYVERN-E 3.0 sensor enumerates."""
import board, busio
MUX_ADDR = 0x70
EXPECT = {0:("BNO085 gimbal",(0x4a,0x4b)),1:("BNO085 FC",(0x4a,0x4b)),2:("BNO085 nose",(0x4a,0x4b)),
          3:("LSM6DSO32",(0x6a,0x6b)),4:("LIS2MDL",(0x1e,)),5:("BMP280",(0x76,0x77)),6:("BME688",(0x76,0x77))}
def scan(i2c):
    while not i2c.try_lock(): pass
    found=[hex(a) for a in i2c.scan()]; i2c.unlock(); return found
i2c = busio.I2C(board.SCL, board.SDA)
print("I2C1 root:", scan(i2c))
import adafruit_tca9548a
mux = adafruit_tca9548a.TCA9548A(i2c, address=MUX_ADDR)
ok = True
for ch,(name,addrs) in EXPECT.items():
    found = scan(mux[ch]); hit = any(hex(a) in found for a in addrs)
    print(f"  ch{ch} {name:14} {'OK ' if hit else 'MISSING'} -> {found}")
    ok &= hit
raise SystemExit(0 if ok else 1)
