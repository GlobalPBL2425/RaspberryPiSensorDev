import time
import os
from multiprocessing import Process, Queue
from sensorClass import sensorReading
from motorClass import MotorPool
from MQTTClass import MQTTFunc
from mysqlClass import  MySQL , Controller
from powerUsage import PowerController
import datetime
import board
from dotenv import load_dotenv

def get_rounded_timestamp(interval):
    now = datetime.datetime.now()
    # Round down the seconds to the nearest multiple of interval
    rounded_seconds = (now.second // interval) * interval
    rounded_now = now.replace(second=rounded_seconds, microsecond=0)
    return rounded_now



# MQTT INFO

arrayName = "Rpi__1"
sensorId = "Sensor_"

sensorPins = [board.D26, board.D19, board.D13]
motorPins = [25, 8 , 7]

if __name__ == "__main__":
    interval = 3
    num_instances = 3
    awsState= False
    awsBool = os.getenv('AWSBOOL')
    if str(awsBool).lower() == 'true':
        awsState = True

    #create lists for motor ids
    rpinames =[]
    # Create lists to hold queues for each instance
    sensor_queues = []
    motorPWM_queues = []
    commandType_queues = []
    threshold_queues = []
    motorstate_queues = []

    # Create lists to hold functions and processes for each instance
    sensorFuncs = []
    motorProcesses =[]

    # Initialize MYSQL functiom
    mySQLFunc = Controller(
        sensorId="Sensor__1",           # Simulated sensor ID
        arrayName= "Rpi__1",
        interval=3,                      # Interval for timestamp rounding in (seconds)
        db_host= os.getenv('DB_HOST'),
        db_port = int(os.getenv('DB_PORT', 3306))  
    )
    
    awsFunc = Controller(
        sensorId="Sensor__1",           # Simulated sensor ID
        arrayName= "Rpi__1",
        interval=3,                      # Interval for timestamp rounding in (seconds)
        db_host= os.getenv('AWS_HOST'),
        db_port = int(os.getenv('AWS_PORT', 3306))  
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
        motorstate_queue = Queue()

        sensor_queues.append(sensor_queue)
        motorPWM_queues.append(motorPWM_queue)
        commandType_queues.append(commandType_queue)
        threshold_queues.append(threshold_queue)
        motorstate_queues.append(motorstate_queue)

        # Initialize functions for each instance
        sensorFunc = sensorReading(sensorPIN=sensorPins[i],sensorID=instance_id)
        
        motor_pool = MotorPool(
            sensor_queue=sensor_queues[i],
            motorpin= motorPins[i],
            threshold_queue=threshold_queues[i],
            motorPWM=motorPWM_queues[i],
            motorstate= motorstate_queues[i],
            daemon=True
        )

        
        motor_pool.start()

        motorProcesses.append(motor_pool)
        sensorFuncs.append(sensorFunc)
        rpinames.append(instance_id) 

    power_pool = PowerController(
        arrayname= arrayName,
         rpiNames=rpinames,
         powerQueueArray=motorstate_queues,
         awsstate= awsState,
         daemon=True 
    )

    mqtt_pool = MQTTFunc( 
        num_instances=num_instances,
        arrayname= arrayName,
        motorThres= threshold_queues,
        commandTypes= commandType_queues, 
        topicNames = rpinames,
        daemon= False
    )

    power_pool.start()
    mqtt_pool.start()

    # Main loop for sensor reading and data handling
    while True:
        for i in range(num_instances):
            sensorFuncs[i].flag = True
            timestamp = get_rounded_timestamp(interval)
            sensor = sensorFuncs[i].readSensor(timestamp)
            if sensor[0] is not None and sensor[1] is not None:
                mySQLFunc.upload(sensor,commandType_queues[i],motorPWM_queues[i])
                if awsState:
                    awsFunc.upload(sensor,commandType_queues[i],motorPWM_queues[i])
                
                if sensor_queues[i].empty():
                    sensor_queues[i].put(sensor)
        time.sleep(interval)  # Sleep based on the interval to avoid rapid looping

    # Wait for processes to complete (if needed)
    for process in processes:
        process.join()



