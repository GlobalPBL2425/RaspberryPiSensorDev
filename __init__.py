import time
import os
import multiprocessing as mp
from awsClass import ControllerPool,AWSSensor
from sensorClass import sensorPool
from motorClass import MotorPool
import datetime




arrayName = "SensorArray_1"
sensorId = "Rpi-sensor_01"


#MQTT topics to confirm that the sensors send the reading to S3 bucket
validotopics = [
    "Rpi-sensor_01",
    "Rpi-sensor_02",
    "Rpi-sensor_03",
    "Rpi-sensor_04",
    "Rpi-sensor_05",
    "Rpi-sensor_06"
]



            
if __name__ == "__main__":
    #initializing the pools
    sensorPool = {}
    motorPool = {}
    controlPool = {}






#master and slave diff
#timing for master()
#send flag to read all sensor
#slaves needs to send back acknowledgement  (publishstatus)
#iot data -----