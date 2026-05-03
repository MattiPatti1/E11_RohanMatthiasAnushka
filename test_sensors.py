#!/usr/bin/env python3
"""Quick test for each sensor individually."""
import time
import board

print("\n--- BME680 ---")
try:
    import adafruit_bme680
    bme = adafruit_bme680.Adafruit_BME680_I2C(board.I2C())
    print(f"Temp: {bme.temperature:.1f} C  Hum: {bme.relative_humidity:.1f}%  Press: {bme.pressure:.1f} hPa")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- SCD30 CO2 ---")
try:
    import adafruit_scd30
    scd = adafruit_scd30.SCD30(board.I2C())
    for _ in range(10):
        time.sleep(2)
        if scd.data_available:
            print(f"CO2: {scd.CO2:.0f} ppm  Temp: {scd.temperature:.1f} C  Hum: {scd.relative_humidity:.1f}%")
            break
    else:
        print("FAIL: no data after 20s")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- MLX90393 Magnetometer ---")
try:
    import adafruit_mlx90393
    mlx = adafruit_mlx90393.MLX90393(board.I2C(), gain=adafruit_mlx90393.GAIN_1X)
    mx, my, mz = mlx.magnetic
    print(f"X: {mx:.1f}  Y: {my:.1f}  Z: {mz:.1f}  uT")
except Exception as e:
    print(f"FAIL: {e}")

print("\nDone.")
