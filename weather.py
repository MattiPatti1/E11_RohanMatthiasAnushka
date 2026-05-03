import adafruit_bme680
import time
import board

# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()   # uses board.SCL and board.SDA
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25


start_time = time.time()
current_time = start_time

while current_time < start_time+5.0:
    t = "Time = " + str(time.asctime())
    T = "\nTemperature: %0.1f C" % bme680.temperature
    G = "Gas: %d ohm" % bme680.gas
    H = "Humidity: %0.1f %%" % bme680.relative_humidity
    P = "Pressure: %0.3f hPa" % bme680.pressure
    A = "Altitude = %0.2f meters" % bme680.altitude
    print(t,T,G,H,P,A)
    current_time = time.time()

    time.sleep(2)
