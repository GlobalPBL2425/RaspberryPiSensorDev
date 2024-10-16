from multiprocessing import Process, Queue
import RPi.GPIO as GPIO
import time

class MotorPool(Process):
    def __init__(self, sensor_queue, daemon):
        Process.__init__(self, daemon=daemon)
        self.sensor_queue = sensor_queue
        self.motorfunc = MotorFunc()

    def run(self):
        while True:
            self.motorfunc.thresholds = thershold_queue
            self.motorfunc.motorcontrol(sensor_queue= self.sensor_queue)


class MotorFunc:
    def pwm(self):
        self.motorpin = 12
        GPIO.setwarnings(False)			#disable warnings
        GPIO.setmode(GPIO.BOARD)		#set pin numbering system
        GPIO.setup(self.motorpin,GPIO.OUT)
        self.pi_pwm = GPIO.PWM(self.motor1pin,1000)		#create PWM instance with frequency
        self.pi_pwm.start(0)				#start PWM of required Duty Cycle 4
        self.thresholds = {
            "min_temp" :20,
            "max_temp" : 35,
            "min_humidity":0,
            "max_humidity":0,
            "time_interval":0,
            "duration":0
        }
        self.commandtype = "auto"
        self.change = False

    def motorcontrol(self, sensor_queue):
        if self.commandtype == "auto":
            if sensor_queue[0] <= self.thresholds["min_temp"]:
                self.pi_pwm.ChangeDutyCycle(100)
            elif self.thresholds["max_temp"] > sensor_queue[0] > self.thresholds["min_temp"]:
                duty = 100 - (sensor_queue[0] - self.thresholds["min_temp"])/(self.thresholds["max_temp"]  - self.thresholds["min_temp"])*100
                self.pi_pwm.ChangeDutyCycle(duty)
            elif sensor_queue[0] >= self.thresholds["max_temp"]:
                self.pi_pwm.ChangeDutyCycle(0)
                
            if sensor_queue[1] <= self.thresholds["min_humidity"]:
                self.pi_pwm.ChangeDutyCycle(100)
            elif self.thresholds["max_humidity"] > sensor_queue[1] > self.thresholds["min_humidity"]:
                duty = 100 - (sensor_queue[1] - self.thresholds["min_humidity"])/(self.thresholds["max_humidity"]  - self.thresholds["min_humidity"])*100
                self.pi_pwm.ChangeDutyCycle(duty)
            elif sensor_queue[1] >= self.thresholds["max_humidity"]:
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
            """
            Runs the PWM for a given `duration` with the ability to interrupt it. 
            After `duration`, it stops the motor for `time_interval` before restarting.
            """
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


