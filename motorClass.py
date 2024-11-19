from multiprocessing import Process, Queue
import RPi.GPIO as GPIO
import time
import threading


class MotorPool(Process):
    def __init__(self, sensor_queue,motorpin ,threshold_queue, motorPWM : Queue, daemon):
        Process.__init__(self,daemon=daemon)
        self.motorpin = motorpin
        self.sensor_queue = sensor_queue
        self.threshold_queue = threshold_queue
        self.motorfunc = MotorFunc()
        self.motorPWM = motorPWM

    def run(self):
        GPIO.setwarnings(False)  # Disable warnings
        #GPIO.setmode(GPIO.Board)  # Set pin numbering system
        GPIO.setup(self.motorpin, GPIO.OUT)

        sensor_reading = None
        while True:

            if not self.sensor_queue.empty():
                sensor_reading = self.sensor_queue.get()

            # Updates the threshold when a new threshold is received via MQTT
            if not self.threshold_queue.empty():
                self.motorfunc.thresholds = self.threshold_queue.get()

            if sensor_reading != None:  # Ensure sensor_reading is not None
                self.motorfunc.motorcontrol(sensor_reading=sensor_reading)
                GPIO.output(self.motorpin, self.motorfunc.motoroutput)
                self.empty_queue()
                self.motorPWM.put(self.motorfunc.duration)
            time.sleep(0.5)  # Small delay to avoid overloading the loop

    def empty_queue(self):  
        while not self.motorPWM.empty():
            try:
                self.motorPWM.get_nowait()  # Non-blocking get to empty the queue
            except:
                break  #


class MotorFunc:
    def __init__(self):
        self.motoroutput = GPIO.LOW
        self.thresholds = {
            "min_temp": 20,
            "max_temp": 35,
            "min_humidity": 0,
            "max_humidity": 100,
            "time_interval": 0,
            "duration": 0
        }
        self.commandtype = "auto"
        self.interval = 0
        self.duration = 0
        self.autotimer = False
        self.timing = False
        self.interrupt_event = threading.Event()
        self.previous_command_type = "auto"

        
    def motorcontrol(self, sensor_reading):
        if self.commandtype != self.previous_command_type:
            print(f"Command type changed from {self.previous_command_type} to {self.commandtype}")
            self.previous_command_type = self.commandtype
            self.interrupt_timer()

        if self.commandtype == "auto":
            if self.timing:
                self.run_timer_with_interrupt(duration=self.duration,interval=self.interval)
                self.timing = False
            else:
                if sensor_reading[0] <= self.thresholds["min_temp"]:
                    temp_duty= 120
                    
                elif self.thresholds["max_temp"] > sensor_reading[0] > self.thresholds["min_temp"]:
                    temp_duty = 120 - (sensor_reading[0] - self.thresholds["min_temp"]) / \
                                (self.thresholds["max_temp"] - self.thresholds["min_temp"]) * 100
                

                # Calculate duty cycles based on humidity
                if sensor_reading[1] <= self.thresholds["min_humidity"]:
                    humidity_duty = 100
                elif self.thresholds["max_humidity"] > sensor_reading[1] > self.thresholds["min_humidity"]:
                    humidity_duty = 100 - (sensor_reading[1] - self.thresholds["min_humidity"]) / \
                                    (self.thresholds["max_humidity"] - self.thresholds["min_humidity"]) * 100
                

                self.timing = True
                if sensor_reading[1] <= self.thresholds["min_humidity"] and sensor_reading[0]  <= self.thresholds["min_temp"]:
                    self.duration = 0 
                    self.interval = 0
                else:
                    self.duration = 1
                    self.interval = (humidity_duty + temp_duty)/2
                

        elif self.commandtype == "timer":
            print("Timer mode activated.")
            # Run the timer with a potential interrupt
            self.run_timer_with_interrupt(self.thresholds["duration"], self.thresholds["time_interval"])


        time.sleep(0.5)  # Small delay to avoid overloading the loop

    def run_timer_with_interrupt(self, duration, time_interval):
        """Runs the PWM for a given `duration` with the ability to interrupt it."""
        self.interrupt_event.clear()  # Clear the event before starting
        print("Starting motor for the timer duration.")
        self.motoroutput = GPIO.HIGH # Full power

        start_time = time.time()
        while time.time() - start_time < duration:
            if self.interrupt_event.is_set():
                print("Timer interrupted!")
                self.motoroutput = GPIO.LOW   # Stop the motor
                return  # Exit the timer

            time.sleep(0.1)  # Check every 0.1 seconds for an interrupt

        self.motoroutput = GPIO.LOW 

        start_time = time.time()
        while time.time() - start_time < time_interval:
            if self.interrupt_event.is_set():
                print("Timer interrupted during the wait interval!")
                return 
            time.sleep(0.1) 


    def interrupt_timer(self):
        """Method to trigger the timer interrupt."""
        self.interrupt_event.set()

    def cleanup(self):
        """Clean up the GPIO settings."""
        GPIO.cleanup()


# Test code for MotorPool process

if __name__ == "__main__":
    # Create queues for inter-process communication
    sensor_queue = Queue()
    threshold_queue = Queue()
    motorPWM_queue = Queue()

    # Initialize MotorPool object with queues and test parameters
    motor_pool = MotorPool(
        sensor_queue=sensor_queue,
        threshold_queue=threshold_queue,
        motorPWM=motorPWM_queue,
        daemon=True
    )

    # Start the MotorPool process
    motor_pool.start()

    # Simulate sensor data (temperature, humidity)
    # Example temperature: 25 degrees Celsius, Humidity: 60%
    sensor_data = (25, 60)
    sensor_queue.put(sensor_data)

    # Simulate new threshold values (could come from an MQTT message in real use)
    # Example thresholds: min_temp: 20, max_temp: 35, min_humidity: 30, max_humidity: 70
    new_thresholds = {
        "min_temp": 20,
        "max_temp": 35,
        "min_humidity": 30,
        "max_humidity": 70,
        "time_interval": 0,
        "duration": 0
    }
    threshold_queue.put(new_thresholds)

    # Let the process run for a while to see the motor control behavior
    time.sleep(5)

    # Retrieve the motor's PWM duty cycle value from the queue
    if not motorPWM_queue.empty():
        pwm_duty = motorPWM_queue.get()
        print(f"Current motor PWM duty cycle: {pwm_duty}%")

    # Stop the MotorPool process after the test
    motor_pool.terminate()
    motor_pool.join()

    print("Test completed.")