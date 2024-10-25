import time
import board
import adafruit_dht
import RPi.GPIO as GPIO
from multiprocessing import Process, Queue, Lock

class GPIOManager:
    """Manages GPIO access to avoid conflicts."""
    _instance = None

    def __init__(self):
        if GPIOManager._instance is not None:
            raise Exception("Only one instance of GPIOManager is allowed!")
        GPIOManager._instance = self
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)  # Set GPIO mode
        self.lock = Lock()  # Lock for synchronized access

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GPIOManager()
        return cls._instance

    def setup_pin(self, pin, mode):
        with self.lock:
            GPIO.setup(pin, mode)

    def cleanup(self):
        with self.lock:
            GPIO.cleanup()

class SensorReading:
    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(board.D16)

    def read_sensor(self):
        try:
            temperature = self.dht_device.temperature
            humidity = self.dht_device.humidity
            return temperature, humidity
        except RuntimeError as error:
            print(f"Sensor error: {error.args[0]}")
            return None, None

class MotorControl:
    def __init__(self):
        self.gpio_manager = GPIOManager.get_instance()
        self.motorpin = 25  # Use GPIO pin 25 for the motor
        self.gpio_manager.setup_pin(self.motorpin, GPIO.OUT)

    def run_motor(self):
        # Example motor control logic
        while True:
            GPIO.output(self.motorpin, GPIO.HIGH)  # Turn the motor on
            print("Motor is ON")
            time.sleep(2)  # Run for 2 seconds
            GPIO.output(self.motorpin, GPIO.LOW)  # Turn the motor off
            print("Motor is OFF")
            time.sleep(2)  # Off for 2 seconds

def sensor_process(sensor_queue):
    sensor = SensorReading()
    while True:
        sensor_data = sensor.read_sensor()
        if sensor_data:
            sensor_queue.put(sensor_data)
        time.sleep(2)  # Adjust reading frequency as needed

def motor_process():
    motor = MotorControl()
    motor.run_motor()

if __name__ == "__main__":
    sensor_queue = Queue()

    # Create and start processes
    p1 = Process(target=sensor_process, args=(sensor_queue,))
    p2 = Process(target=motor_process)

    p1.start()
    p2.start()

    try:
        while True:
            # Main process can perform other tasks if needed
            if not sensor_queue.empty():
                temperature, humidity = sensor_queue.get()
                print(f"Received Sensor Data: Temperature: {temperature}°C, Humidity: {humidity}%")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating processes...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()
        GPIOManager.get_instance().cleanup()  # Cleanup GPIO
        print("GPIO cleaned up and processes terminated.")
