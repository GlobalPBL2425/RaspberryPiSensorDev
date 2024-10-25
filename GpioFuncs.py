import time
import board
import adafruit_dht
import datetime
import RPi.GPIO as GPIO
from multiprocessing import Process, Queue

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
            # Read and queue sensor data if queue is empty
            if self.sensor_queue.empty():
                sensor_data = self.sensorFunc.read_sensor()
                self.sensor_queue.put(sensor_data)

            # Get the latest sensor reading and thresholds, and update motor control
            if not self.sensor_queue.empty():
                sensor_reading = self.sensor_queue.get()
                self.motorFunc.motorcontrol(sensor_reading)

            if not self.threshold_queue.empty():
                self.motorFunc.thresholds = self.threshold_queue.get()

            # Send the duty cycle to motorPWM queue
            self.motorFunc.update_duty_cycle(self.motorPWM)

            time.sleep(0.5)  # Small delay to avoid overloading the loop

    def cleanup(self):
        """Clean up GPIO settings on exit."""
        self.motorFunc.cleanup()
        GPIO.cleanup()


class MotorFunc:
    def __init__(self):
        self.motorpin = 25
        self.setup_gpio()
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

    def setup_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.motorpin, GPIO.OUT)
        self.pi_pwm = GPIO.PWM(self.motorpin, 1000)  # PWM with frequency 1kHz
        self.pi_pwm.start(0)

    def motorcontrol(self, sensor_reading):
        # Motor control logic for temperature and humidity
        temp, humidity = sensor_reading
        if self.commandtype == "auto":
            # Temperature control
            if temp <= self.thresholds["min_temp"]:
                self.set_duty_cycle(100)
            elif temp >= self.thresholds["max_temp"]:
                self.set_duty_cycle(0)
            else:
                duty = 100 - (temp - self.thresholds["min_temp"]) / (self.thresholds["max_temp"] - self.thresholds["min_temp"]) * 100
                self.set_duty_cycle(duty)

            # Humidity control
            if humidity <= self.thresholds["min_humidity"]:
                self.set_duty_cycle(100)
            elif humidity >= self.thresholds["max_humidity"]:
                self.set_duty_cycle(0)
            else:
                duty = 100 - (humidity - self.thresholds["min_humidity"]) / (self.thresholds["max_humidity"] - self.thresholds["min_humidity"]) * 100
                self.set_duty_cycle(duty)

    def set_duty_cycle(self, duty):
        self.pi_pwm.ChangeDutyCycle(duty)
        self.dutycycle = duty

    def update_duty_cycle(self, motorPWM: Queue):
        while not motorPWM.empty():
            motorPWM.get_nowait()  # Clear queue
        motorPWM.put(self.dutycycle)

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


# Example usage
if __name__ == "__main__":
    sensor_queue = Queue()
    threshold_queue = Queue()
    motorPWM = Queue()

    motor_sensor_process = MotorAndSensorControl(sensor_queue=sensor_queue, threshold_queue=threshold_queue, motorPWM=motorPWM, daemon=True)
    motor_sensor_process.start()

    try:
        while True:
            time.sleep(1)  # Keep main loop running
    except KeyboardInterrupt:
        motor_sensor_process.cleanup()
        motor_sensor_process.terminate()