import time
import os
import multiprocessing as mp

from sensorClass import sensorReading
import datetime

controller = "master"

arrayName = "SensorArray_1"
sensorId = "Rpi-sensor_01"


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
            
        

class Master():
    def __init__(self , master ,timing):
        self.master = master
        self.timing = timing*60
        self.sensor = 

    def timing():

    def



class Slave():
    


if __name__ == "__main__":
    #initializing the pools
    seneor_queue = Queue
    sensorPool = {}


#master and slave diff
#timing for master()
#send flag to read all sensor