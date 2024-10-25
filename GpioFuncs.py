import time
import board
import adafruit_dht
import datetime
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
        GPIO.setmode(GPIO.BOARD)
        self.lock = Lock()  # Lock for synchronized access

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GPIOManager()
        return cls._instance

    def setup_pin(self, pin, mode):
        with self.lock:
            GPIO.setup(pin, mode)

    def pwm_start(self, pin, frequency):
        with self.lock:
            pwm = GPIO.PWM(pin, frequency)
            pwm.start(0)
            return pwm

    def cleanup(self):
        with self.lock:
            GPIO.cleanup()


class MotorFunc:
    def __init__(self):
        self.gpio_manager = GPIOManager.get_instance()
        self.motorpin = 25
        self.gpio_manager.setup_pin(self.motorpin, GPIO.OUT)
        self.pi_pwm = self.gpio_manager.pwm_start(self.motorpin, 1000)
        self.thresholds = {
            "min_temp": 20,
            "max_temp": 35,
            "min_humidity": 0,
            "max_humidity": 100,
            "time_interval": 0,
            "duration": 0
        }
        self.commandtype = "auto"
        self.dutycycle = 0

    def motorcontrol(self, sensor_reading):
        temp, humidity = sensor_reading
        if self.commandtype == "auto":
            duty = self.calculate_duty(temp, self.thresholds["min_temp"], self.thresholds["max_temp"])
            self.set_duty_cycle(duty)
            
            duty = self.calculate_duty(humidity, self.thresholds["min_humidity"], self.thresholds["max_humidity"])
            self.set_duty_cycle(duty)

    def calculate_duty(self, value, min_threshold, max_threshold):
        if value <= min_threshold:
            return 100
        elif value >= max_threshold:
            return 0
        else:
            return 100 - (value - min_threshold) / (max_threshold - min_threshold) * 100

    def set_duty_cycle(self, duty):
        self.dutycycle = duty
        self.pi_pwm.ChangeDutyCycle(duty)

    def cleanup(self):
        self.pi_pwm.stop()


class SensorReading:
    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(board.D16)

    def read_sensor(self):
        try:
            temperature = self.dht_device.temperature
            humidity = self.dht_device.humidity
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            return temperature, humidity
        except RuntimeError as error:
            print(f"Sensor error: {error.args[0]}")
            return None, None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None, None


class MotorAndSensorControl(Process):
    def __init__(self, sensor_queue: Queue, threshold_queue: Queue, motorPWM: Queue, daemon):
        super().__init__(daemon=daemon)
        self.sensorFunc = SensorReading()
        self.motorFunc = MotorFunc()
        self.sensor_queue = sensor_queue
        self.threshold_queue = threshold_queue
        self.motorPWM = motorPWM

    def run(self):
        while True:
            if self.sensor_queue.empty():
                sensor_data = self.sensorFunc.read_sensor()
                if sensor_data:
                    self.sensor_queue.put(sensor_data)

            if not self.sensor_queue.empty():
                sensor_reading = self.sensor_queue.get()
                self.motorFunc.motorcontrol(sensor_reading)

            if not self.threshold_queue.empty():
                self.motorFunc.thresholds = self.threshold_queue.get()

            self.motorFunc.set_duty_cycle(self.motorFunc.dutycycle)
            time.sleep(0.5)

    def cleanup(self):
        self.motorFunc.cleanup()
        GPIOManager.get_instance().cleanup()


# Example usage
if __name__ == "__main__":
    sensor_queue = Queue()
    threshold_queue = Queue()
    motorPWM = Queue()

    motor_sensor_process = MotorAndSensorControl(sensor_queue=sensor_queue, threshold_queue=threshold_queue, motorPWM=motorPWM, daemon=True)
    motor_sensor_process.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        motor_sensor_process.cleanup()
        motor_sensor_process.terminate()
