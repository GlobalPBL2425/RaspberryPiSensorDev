import time
import os
import multiprocessing as mp
from awsClass import Slave, Master,AWSSensor
from sensorClass import sensorReading
import datetime

controller = "master"

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



class Controller:
    def __init__(self , master ,timing):
        self.master = master
        self.timing = timing*60
        self.sensor = sensorPool
        self.masterFunc = None
        self.slaveFunc = None

    def on_start(self):
        #to set the rpi up as slave of master
        if self.master:
            self.masterFunc = Master()
        else:
            self.slaveFunc = Slave()

    def mainFunc(self):
        if self.master:
            
        else:
            
if __name__ == "__main__":
    #initializing the pools
    sensorPool = {}


#master and slave diff
#timing for master()
#send flag to read all sensor
#slaves needs to send back acknowledgement  (publishstatus)
#iot data -----