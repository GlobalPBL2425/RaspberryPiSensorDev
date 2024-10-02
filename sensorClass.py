import time
import board
import adafruit_dht
from plotterClass import plotterFunc
class sensorFunc:
    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(board.D16)
        self.startTime = None
        self.datetime
    def startTime(self):
        start_time = time.time()


    def readSensor(self):
        while True:
            try:
                # Read temperature and humidity from the sensor
                temperature = self.dht_device.temperature
                humidity = self.dht_device.humidity
                current_time = time.time() - self.start_time  # Calculate time elapsed

                if temperature is not None and humidity is not None:
                    print(f"Temperature: {temperature:.1f} °C    Humidity: {humidity:.1f}%")
                    
                    # Append the new data to the deques
                    temperature_data.append(temperature)
                    humidity_data.append(humidity)
                    time_data.append(current_time)
                    
                    # Update the plot with the new data
                    update_plot()

                else:
                    print("Failed to retrieve data from the sensor")

            except RuntimeError as error:
                # Errors happen occasionally, just try again
                print(f"Error: {error.args[0]}")
                time.sleep(2.0)
                continue