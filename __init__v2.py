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
commandTopic = "GPBL2425/controlType"
motorTopic = "GBPL2425/Motor/threshold"
arrayName = "SensorArray_1"
sensorId = "Rpi_"

# Sensor Name Prefix
SensorName  = "Sensor_"

if __name__ == "__main__":
    interval = 3
    num_instances = 3  # Number of instances to run

    # Create lists to hold queues and processes for each instance
    sensor_queues = []
    motorPWM_queues = []
    commandType_queues = []
    threshold_queues = []
    processes = []

    for i in range(num_instances):
        # Initialize unique identifiers for each instance
        instance_id = f"{sensorId}_{i + 1}"
        instance_array = f"arrayName"

        # Initialize queues for each instance
        sensor_queue = Queue()
        motorPWM_queue = Queue()
        commandType_queue = Queue()
        threshold_queue = Queue()

        # Append queues to lists for later access if needed
        sensor_queues.append(sensor_queue)
        motorPWM_queues.append(motorPWM_queue)
        commandType_queues.append(commandType_queue)
        threshold_queues.append(threshold_queue)

        # Initialize sensor reading object
        sensorFunc = sensorReading(sensorID=board.D16)

        # Initialize motor, controller, and MQTT processes
        motor_pool = MotorPool(
            sensor_queue=sensor_queue,
            threshold_queue=threshold_queue,
            motorpin= 25,
            motorPWM=motorPWM_queue,
            daemon=True
        )

        controllerpool = ControllerPool(
            sensorId=instance_id,
            arrayName=instance_array,
            sensor_queue=sensor_queue,
            interval=interval,
            motorPWM=motorPWM_queue,
            commandType=commandType_queue,
            ip="localhost",
            daemon=True
        )

        mqtt_pool = MQTTFunc(
            commandTopic=commandTopic,
            motorTopic=motorTopic,
            sensorqueue=sensor_queue,
            mqtt_broker=mqtt_broker,
            motorThres=threshold_queue,
            commandType=commandType_queue,
            mqtt_port=mqtt_port,
            daemon=False
        )

        # Append each process to the processes list and start them
        processes.append(controllerpool)
        processes.append(motor_pool)
        processes.append(mqtt_pool)

        # Start processes
        controllerpool.start()
        motor_pool.start()
        mqtt_pool.start()

        # Main loop for sensor reading and data handling
        while True:
            sensorFunc.flag = True
            timestamp = get_rounded_timestamp(interval)
            sensor = sensorFunc.readSensor(timestamp)

            if sensor_queue.empty():
                sensor_queue.put(sensor)
            time.sleep(interval)  # Sleep based on the interval to avoid rapid looping

    # Wait for processes to complete (if needed)
    for process in processes:
        process.join()
