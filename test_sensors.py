#!/usr/bin/env python3
"""Quick test for every sensor individually."""
import time
import board

print("\n--- BME680 (env) ---")
try:
    import adafruit_bme680
    bme = adafruit_bme680.Adafruit_BME680_I2C(board.I2C())
    print(f"OK  Temp: {bme.temperature:.1f}C  Hum: {bme.relative_humidity:.1f}%  Press: {bme.pressure:.1f}hPa")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- SCD30 (CO2) ---")
try:
    import adafruit_scd30
    scd = adafruit_scd30.SCD30(board.I2C())
    for _ in range(10):
        time.sleep(2)
        if scd.data_available:
            print(f"OK  CO2: {scd.CO2:.0f}ppm  Temp: {scd.temperature:.1f}C  Hum: {scd.relative_humidity:.1f}%")
            break
    else:
        print("FAIL: no data after 20s")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- MLX90393 (magnetometer) ---")
try:
    import adafruit_mlx90393
    mlx = adafruit_mlx90393.MLX90393(board.I2C(), gain=adafruit_mlx90393.GAIN_1X)
    mx, my, mz = mlx.magnetic
    print(f"OK  X: {mx:.1f}  Y: {my:.1f}  Z: {mz:.1f}  uT")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- PM2.5 (dust) ---")
try:
    import serial
    from adafruit_pm25.uart import PM25_UART
    uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.25)
    pm = PM25_UART(uart, reset_pin=None)
    r = pm.read()
    print(f"OK  PM1: {r['pm10 standard']}  PM2.5: {r['pm25 standard']}  PM10: {r['pm100 standard']}  ug/m3")
except Exception as e:
    print(f"FAIL: {e}")

print("\n--- MCA (radiation) ---")
try:
    from capemca import CapeMCA, find_all_mcas
    if not find_all_mcas():
        print("FAIL: no MCA device found")
    else:
        with CapeMCA() as mca:
            s = mca.read_status()
            print(f"OK  CPS: {s.cps}  Total: {s.total_count}")
except Exception as e:
    print(f"FAIL: {e}")

print("\nDone.")
