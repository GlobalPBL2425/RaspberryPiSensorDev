import time
import board
import adafruit_dht
from plotterClass import plotterFunc
from csvClass import csvFunc
import datetime

class sensorFunc:
    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(board.D16)
        self.startTime = None
        self.plot = plotterFunc()

    def readSensor(self):
        while True:
            try:
                
                # Read temperature and humidity from the sensor
                temperature = self.dht_device.temperature
                humidity = self.dht_device.humidity
                currtime = datetime.datetime.now()
                formatted_time = currtime.strftime('%Y-%m-%d %H:%M:%S')  # Calculate time elapsed

                self.plot.plotingFunc(temperature , humidity , formatted_time)

            
            except RuntimeError as error:
                # Errors happen occasionally, just try again
                print(f"Error: {error.args[0]}")
                time.sleep(2.0)
                continue