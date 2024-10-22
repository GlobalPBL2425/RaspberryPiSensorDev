from multiprocessing import Process, Queue
import RPi.GPIO as GPIO
import time

class MotorPool(Process):
    def __init__(self, sensor_queue, threshold_queue, daemon):
        super().__init__(daemon=daemon)
        self.sensor_queue = sensor_queue
        self.threshold_queue = threshold_queue
        self.motorfunc = MotorFunc()

    def run(self):
        while True:
            if not self.sensor_reading.empty():
                sensor_reading = self.sensor_reading.get()

            # Updates the threshold when a new threshold is received via MQTT
            if not self.threshold_queue.empty():
                self.motorfunc.thresholds = self.threshold_queue.get()

            if sensor_reading:  # Ensure sensor_reading is not None
                self.motorfunc.motorcontrol(sensor_reading=sensor_reading)
            time.sleep(0.5)  # Small delay to avoid overloading the loop

    def get_latest_queue_item(self, sensor_queue):
        latest_data = None
        while not sensor_queue.empty():
            try:
                # Continuously get items from the queue, overwriting old data
                latest_data = sensor_queue.get_nowait()
            except Exception as e:
                print(f"Error retrieving from sensor queue: {e}")
                break

        return latest_data


class MotorFunc:
    def __init__(self):
        self.motorpin = 12
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
        self.change = False

    def setup_gpio(self):
        GPIO.setwarnings(False)  # Disable warnings
        GPIO.setmode(GPIO.BOARD)  # Set pin numbering system
        GPIO.setup(self.motorpin, GPIO.OUT)
        self.pi_pwm = GPIO.PWM(self.motorpin, 1000)  # Create PWM instance with frequency
        self.pi_pwm.start(0)  # Start PWM with 0 Duty Cycle

    def motorcontrol(self, sensor_reading):
        if self.commandtype == "auto":
            if sensor_reading[0] <= self.thresholds["min_temp"]:
                self.pi_pwm.ChangeDutyCycle(100)
            elif self.thresholds["max_temp"] > sensor_reading[0] > self.thresholds["min_temp"]:
                duty = 100 - (sensor_reading[0] - self.thresholds["min_temp"]) / (self.thresholds["max_temp"] - self.thresholds["min_temp"]) * 100
                self.pi_pwm.ChangeDutyCycle(duty)
            elif sensor_reading[0] >= self.thresholds["max_temp"]:
                self.pi_pwm.ChangeDutyCycle(0)

            if sensor_reading[1] <= self.thresholds["min_humidity"]:
                self.pi_pwm.ChangeDutyCycle(100)
            elif self.thresholds["max_humidity"] > sensor_reading[1] > self.thresholds["min_humidity"]:
                duty = 100 - (sensor_reading[1] - self.thresholds["min_humidity"]) / (self.thresholds["max_humidity"] - self.thresholds["min_humidity"]) * 100
                self.pi_pwm.ChangeDutyCycle(duty)
            elif sensor_reading[1] >= self.thresholds["max_humidity"]:
                self.pi_pwm.ChangeDutyCycle(0)

        elif self.commandtype == "timer":
            self.change = True
            print("Timer mode activated.")
            # Run the timer with a potential interrupt
            self.run_timer_with_interrupt(self.thresholds["duration"], self.thresholds["time_interval"])

        if self.change:
            self.interrupt_timer()
            self.change = False
        time.sleep(0.5)  # Small delay to avoid overloading the loop

    def run_timer_with_interrupt(self, duration, time_interval):
        """Runs the PWM for a given `duration` with the ability to interrupt it."""
        self.interrupt_event.clear()  # Clear the event before starting
        print("Starting motor for the timer duration.")
        self.pi_pwm.ChangeDutyCycle(100)  # Full power

        start_time = time.time()
        while time.time() - start_time < duration:
            if self.interrupt_event.is_set():
                print("Timer interrupted!")
                self.pi_pwm.ChangeDutyCycle(0)  # Stop the motor
                return  # Exit the timer

            time.sleep(0.1)  # Check every 0.1 seconds for an interrupt

        # Motor stop after duration
        self.pi_pwm.ChangeDutyCycle(0)
        print("Stopping motor after duration.")
        time.sleep(time_interval)

    def interrupt_timer(self):
        """Method to trigger the timer interrupt."""
        self.interrupt_event.set()

    def cleanup(self):
        """Clean up the GPIO settings."""
        self.pi_pwm.stop()
        GPIO.cleanup()
