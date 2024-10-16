from multiprocessing import Process, Queue
import RPi.GPIO as GPIO

class MotorPool:
    def __init__(self , daemon):
        Process.__init__(self, daemon=daemon)

class MotorFunc:
    def pwm(self):
        self.motorpin = 12
        GPIO.setwarnings(False)			#disable warnings
        GPIO.setmode(GPIO.BOARD)		#set pin numbering system
        GPIO.setup(self.motorpin,GPIO.OUT)
        pi_pwm = GPIO.PWM(self.motor1pin,1000)		#create PWM instance with frequency
        pi_pwm.start(0)				#start PWM of required Duty Cycle 