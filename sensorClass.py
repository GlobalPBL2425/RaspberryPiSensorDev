import time
import board
import adafruit_dht
from plotterClass import plotterFunc
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
    def empty_queue(self):  
        while not self.sensor_queue.empty():
            try:
                self.sensor_queue.get_nowait()  # Non-blocking get to empty the queue
            except:
                break  #


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



#Testing Function
def test_sensor_pool():
    # Create a Queue to communicate between processes
    sensor_queue = Queue()

    # Initialize the sensorPool as a separate process
    sensor_process = sensorPool(sensor_queue=sensor_queue, daemon=False)

    # Start the sensor process
    sensor_process.start()

    # Run the test for a few seconds to gather sensor data
    try:
        start_time = time.time()
        while True:  
            if not sensor_queue.empty():
                sensor_data = sensor_queue.get()
                temperature, humidity = sensor_data
                print(f"Test - Sensor Data Received: Temperature: {temperature}, Humidity: {humidity}")
                # Clear the queue (removing any leftover items)
                while not sensor_queue.empty():
                    sensor_queue.get()#most important line
                
            else:
                print("Waiting for sensor data...")
            time.sleep(1)  # Poll the queue every second
    except KeyboardInterrupt:
        print("Test interrupted.")
    finally:
        # Ensure the sensor process is terminated after the test
        sensor_process.terminate()
        sensor_process.join()

if __name__ == "__main__":
    test_sensor_pool()