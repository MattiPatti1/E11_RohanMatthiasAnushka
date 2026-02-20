import time
import csv 
import time
import sys
import numpy as np 
import board
import busio
import adafruit_bme680

from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
reset_pin = None
import serial
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.25)
from adafruit_pm25.uart import PM25_UART
pm25 = PM25_UART(uart, reset_pin)

# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()   # uses board.SCL and board.SDA
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25

print("Found PM2.5 sensor, reading data about the concentration of different sized particles.")

arguments = sys.argv
print(arguments)

data_path = arguments[0]
runtime = int(arguments[1])

file = open(data_path,'w', newline = None)

csvwriter = csv.writer(file, delimiter=',')

meta = ['time','data']
csvwriter.writerow(meta)


start_time = time.time()
current_time = start_time

while current_time < start_time+runtime:
    t = "Time = " + str(time.asctime())
    time.sleep(1)
    T = "\nTemperature: %0.1f C" % bme680.temperature
    G = "Gas: %d ohm" % bme680.gas
    H = "Humidity: %0.1f %%" % bme680.relative_humidity
    P = "Pressure: %0.3f hPa" % bme680.pressure
    A = "Altitude = %0.2f meters" % bme680.altitude
    print(t,T,G,H,P,A)
    current_time = time.time()

    try:
        aqdata = pm25.read()
        # print(aqdata)
    except RuntimeError:
        print("Unable to read from sensor, retrying...")
    current_time = time.time()

    print()
    print(t) 
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
    )
    print("Concentration Units (environmental)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
    )
    print("---------------------------------------")
    print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
    print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
    print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
    print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
    print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
    print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
    print("---------------------------------------")


file = open('Week5Data.csv', 'w', newline='')
csvwriter = csv.writer(file, delimiter=',')


file.write("# PM25 sensor log from Raspberry Pi")

csvwriter.writerow([
    "timestamp",
    "pm1_standard",
    "pm25_standard",
    "pm10_standard",
    "Temperature",
    "Gas",
    "Humidity",
    "Pressure",
    "Altitude",
])

start_time = time.time()

while time.time() - start_time < runtime:   # run for 30 seconds

    try:
        aqdata = pm25.read()
    except RuntimeError:
        print("Read error, skipping sample")
        continue

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    csvwriter.writerow([
        timestamp,
        aqdata["pm10 standard"],
        aqdata["pm25 standard"],
        aqdata["pm100 standard"],
        T,
        G,
        H,
        P,
        A,
    ])
    
    time.sleep(1)





