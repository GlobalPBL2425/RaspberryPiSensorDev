import time
import os
from multiprocessing import Process, Queue
from sensorClass import sensorReading
from motorClass import MotorPool
from MQTTClass import MQTTFunc
from mysqlClass import ControllerPool
import datetime
import board

def get_rounded_timestamp(interval):
    now = datetime.datetime.now()
    # Round down the seconds to the nearest multiple of interval
    rounded_seconds = (now.second // interval) * interval
    rounded_now = now.replace(second=rounded_seconds, microsecond=0)
    return rounded_now

# MQTT INFO
mqtt_broker = "test.mosquitto.org"
mqtt_port = 1883
commandTopic = "GPBL2425/controlType"  ###(update this so that it is individual rpi)
motorTopic = "GBPL2425/Motor/threshold"
arrayName = "SensorArray_1"
sensorId = "Rpi_"

sensorPins = [board.D16, board.D1]
motorPins = [25,10]

if __name__ == "__main__":
    interval = 3
    num_instances = 3

    # Create lists to hold queues and processes for each instance
    sensor_queues = []

    # Create lists to hold functions and processes for each instance
    sensorFuncs = []

    for i in range(num_instances):
        # Initialize unique identifiers for each instance
        instance_id = f"{sensorId}_{i + 1}"
        instance_array = f"arrayName"

        # Initialize queues for each instance
        sensor_queue = Queue()
        
        sensor_queues.append(sensor_queue)

        # Initialize functions for each instance
        sensorFunc = sensorReading(sensorID=sensorPins[i])


        sensorFuncs.append(sensorFunc)


    # Main loop for sensor reading and data handling
    while True:
        for i in range(num_instances):
            sensorFuncs[i].flag = True
            timestamp = get_rounded_timestamp(interval)
            sensor = sensorFuncs[i].readSensor(timestamp)

            if sensor_queues[i].empty():
                sensor_queues[i].put(sensor)
        time.sleep(interval)  # Sleep based on the interval to avoid rapid looping

    # Wait for processes to complete (if needed)
    for process in processes:
        process.join()
