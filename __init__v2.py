import time
import os
from multiprocessing import Process, Queue
from sensorClass import sensorReading
from motorClass import MotorPool
from MQTTClass import MQTTFunc
from mysqlClass import ControllerPool , MySQL , Controller
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
    num_instances = 2

    # Create lists to hold queues for each instance
    sensor_queues = []
    motorPWM_queues = []
    commandType_queues = []
    threshold_queues = []

    # Create lists to hold functions and processes for each instance
    sensorFuncs = []
    motorProcesses =[]

    # Initialize MYSQL functiom
    mySQLFunc = Controller(
        sensorId="Sensor_001",           # Simulated sensor ID
        arrayName= "Group1",
        interval=3,                      # Interval for timestamp rounding in (seconds)
        ip="192.168.11.4"  
    )

    for i in range(num_instances):
        # Initialize unique identifiers for each instance
        instance_id = f"{sensorId}_{i + 1}"
        instance_array = f"arrayName"

        # Initialize queues for each instance
        sensor_queue = Queue()
        motorPWM_queue = Queue()
        commandType_queue = Queue()
        threshold_queue = Queue()

        sensor_queues.append(sensor_queue)
        motorPWM_queues.append(motorPWM_queue)
        commandType_queues.append(commandType_queue)
        threshold_queues.append(threshold_queue)

        # Initialize functions for each instance
        sensorFunc = sensorReading(sensorPIN=sensorPins[i],sensorID=instance_id)
        
        motor_pool = MotorPool(
            sensor_queue=sensor_queues[i],
            motorpin= motorPins[i],
            threshold_queue=threshold_queues[i],
            motorPWM=motorPWM_queues[i],
            daemon=True
        )
        motor_pool.start
        
        motorProcesses.append(motor_pool)
        sensorFuncs.append(sensorFunc)

    mqtt_pool = MQTTFunc( 
        mqtt_broker= mqtt_broker, 
        mqtt_port= mqtt_port, 
        num_instances=num_instances,
        arrayname= arrayName,
        motorThres= threshold_queues,
        commandType= commandType_queues, 
        daemon= False
    )

    # Main loop for sensor reading and data handling
    while True:
        for i in range(num_instances):
            sensorFuncs[i].flag = True
            timestamp = get_rounded_timestamp(interval)
            sensor = sensorFuncs[i].readSensor(timestamp)

            mySQLFunc.upload(sensor,commandType_queues[i],motorPWM_queues[i])
            

            if sensor_queues[i].empty():
                sensor_queues[i].put(sensor)
        time.sleep(interval)  # Sleep based on the interval to avoid rapid looping

    # Wait for processes to complete (if needed)
    for process in processes:
        process.join()


