import time
import os
from multiprocessing import Process, Queue
from sensorClass import sensorPool
from motorClass import MotorPool
from MQTTClass import MQTTFunc
from mysqlClass import ControllerPool
import datetime


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





            
if __name__ == "__main__":
    #inititalizing tthe queues
    sensor_queue = Queue()
    motorPWM_queue = Queue()
    commandType_queue = Queue()
    threshold_queue = Queue()

    #initializing the pools
    sensor_pool = sensorPool(
        sensor_queue=sensor_queue,
        daemon=False
    )
    motor_pool = MotorPool()
    controllerpool = ControllerPool()
    mqtt_pool = MQTTFunc()


#master and slave diff
#timing for master()
#send flag to read all sensor
#slaves needs to send back acknowledgement  (publishstatus)
#iot data -----