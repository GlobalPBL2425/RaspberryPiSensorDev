import time
import board
import adafruit_dht
from plotterClass import plotterFunc
from csvClass import csvFunc
import datetime
from multiprocessing import Process, Queue

class sensorPool(Process):
    def __init__(self, sensor_queue:Queue, daemon):
        Process.__init__(self, daemon=daemon)
        self.sensorFunc = sensorReading()
        self.sensor_queue = sensor_queue
    def run(self):
        while True:
            self.sensorFunc.flag = True
            sensor = self.sensorFunc.readSensor()
            if self.sensor_queue.empty():
                    self.sensor_queue.put(sensor)

            


class sensorReading:
    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(board.D16)
        self.instance = [0,0]
        self.flag = False

    def readSensor(self):
        #try to read the temperature
        while self.flag:
            try:
                # Read temperature and humidity from the sensor
                temperature = self.dht_device.temperature
                humidity = self.dht_device.humidity
                currtime = datetime.datetime.now()
                formatted_time = currtime.strftime('%Y-%m-%d %H:%M:%S')

                # Store the values in self.instance
                self.instance = [temperature, humidity]
                print(f"Local Time: {formatted_time}, Temp: {temperature}, Humidity: {humidity}")
                
                self.flag = False
                return self.instance
            except RuntimeError as error:
                # repeats until gets temperature
                print(f"Error: {error.args[0]}")
                continue
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                continue 

        

