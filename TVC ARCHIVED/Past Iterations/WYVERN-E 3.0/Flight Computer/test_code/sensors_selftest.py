#!/usr/bin/env python3
"""Read one sample from all WYVERN-E 3.0 sensors through the TCA9548A. Exit 0 if all respond."""
import time, board, busio, adafruit_tca9548a
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_lsm6ds.lsm6dso32 import LSM6DSO32
import adafruit_lis2mdl, adafruit_bmp280, adafruit_bme680
i2c = busio.I2C(board.SCL, board.SDA)
mux = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
fail = []
def bno(ch, tag):
    try:
        d = BNO08X_I2C(mux[ch]); d.enable_feature(BNO_REPORT_ROTATION_VECTOR); time.sleep(0.3)
        q = d.quaternion; print(f"  BNO085 {tag:7} quat={tuple(round(v,3) for v in q)}")
    except Exception as e: fail.append(f"BNO085 {tag}: {e}")
bno(0,"gimbal"); bno(1,"FC"); bno(2,"nose")
try: a=LSM6DSO32(mux[3]); print(f"  LSM6DSO32 accel={tuple(round(v,2) for v in a.acceleration)} gyro={tuple(round(v,2) for v in a.gyro)}")
except Exception as e: fail.append(f"LSM6DSO32: {e}")
try: m=adafruit_lis2mdl.LIS2MDL(mux[4]); print(f"  LIS2MDL mag={tuple(round(v,1) for v in m.magnetic)}")
except Exception as e: fail.append(f"LIS2MDL: {e}")
try: b=adafruit_bmp280.Adafruit_BMP280_I2C(mux[5]); print(f"  BMP280 P={b.pressure:.1f}hPa T={b.temperature:.1f}C")
except Exception as e: fail.append(f"BMP280: {e}")
try: g=adafruit_bme680.Adafruit_BME680_I2C(mux[6]); print(f"  BME688 T={g.temperature:.1f}C RH={g.humidity:.0f}% gas={g.gas}ohm")
except Exception as e: fail.append(f"BME688: {e}")
if fail: print("FAIL:"); [print("   ",x) for x in fail]; raise SystemExit(1)
print("ALL SENSORS OK"); raise SystemExit(0)
