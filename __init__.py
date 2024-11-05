import time
import os
from multiprocessing import Process, Queue
from sensorClass import sensorReading
from motorClass import MotorPool
from MQTTClass import MQTTFunc
from mysqlClass import ControllerPool
import datetime

def get_rounded_timestamp(interval):
        now = datetime.datetime.now()
        # Always round down the seconds to the nearest multiple of 3 (i.e., 0, 3, 6, 9, ...)
        rounded_seconds = (now.second // interval) * interval
        rounded_now = now.replace(second=rounded_seconds, microsecond=0)
        return rounded_now


"""
MQTT INFO 
# MQTT
mqtt_broker = "test.mosquitto.org"
mqtt_port = 1883
topics = 
arrayName = "SensorArray_1"
sensorId = "Rpi_01" 
"""

#MQTT topics to confirm that the sensors send the reading to S3 bucket
mqtt_broker = "test.mosquitto.org"
mqtt_port = 1883
commandTopic = "GPBL2425/controlType"
motorTopic = "GBPL2425/Motor/threshold"

arrayName = "SensorArray_1"
sensorId = "Rpi_01"


SensorName  = "Sensor_" 


            
if __name__ == "__main__":
    #inititalizing tthe queues
    sensor_queue = Queue()
    motorPWM_queue = Queue()
    commandType_queue = Queue()
    threshold_queue = Queue()

    #initializing the pools
    """
    sensor_pool = sensorPool(
        sensor_queue=sensor_queue,
        daemon=False
    )
    """
    sensorFunc = sensorReading()

    motor_pool = MotorPool(
        sensor_queue=sensor_queue,
        threshold_queue=threshold_queue,
        motorPWM=motorPWM_queue,
        daemon=True
    )
    
    controllerpool = ControllerPool(sensorId="Sensor_001",           # Simulated sensor ID
        arrayName= "Group1",
        sensor_queue=sensor_queue,       # Queue for sensor data
        interval=3,                      # Interval for timestamp rounding in (seconds)
        motorPWM=motorPWM_queue,         # Queue for motor PWM control
        commandType=commandType_queue,   # Queue for control type (AUTO/TIMER)
        ip="localhost",
        daemon=True      )
    
    mqtt_pool = MQTTFunc(
        commandTopic= commandTopic, 
        motorTopic= motorTopic, 
        sensorqueue= sensor_queue, 
        mqtt_broker= mqtt_broker, 
        motorThres= threshold_queue,
        commandType= commandType_queue, 
        mqtt_port= mqtt_port, 
        daemon= False
    )

    #sensor_pool.start()
    controllerpool.start()
    motor_pool.start()
    mqtt_pool.start()

    while True:
            sensorFunc.flag = True
            sensor = sensorFunc.readSensor()
            
            if sensor_queue.empty():
                sensor_queue.put(sensor)

#master and slave diff
#timing for master()
#send flag to read all sensor
#slaves needs to send back acknowledgement  (publishstatus)
#iot data -----