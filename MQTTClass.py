from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import time
from dotenv import load_dotenv
import os
from mysqlClass import thresholdSQL
import datetime

class MQTTFunc(Process):
    def __init__(self, num_instances, arrayname, motorThres : list[Queue], commandTypes: list[Queue], topicNames ,daemon):
        Process.__init__(self, daemon=daemon)
        load_dotenv()

        # Retrieve database credentials from environment variables
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT', 3306))  # Use default port 3306 if not specified
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        db_charset = os.getenv('DB_CHARSET', 'utf8mb4')  # Default to 'utf8mb4'
        self.sql = thresholdSQL( db_host, db_port, db_user, db_password, db_name, db_charset)

        
        aws_host = os.getenv('AWS_HOST')
        aws_port = int(os.getenv('AWS_PORT', 3306))  # Use default port 3306 if not specified
        aws_user = os.getenv('DB_USER')
        aws_password = os.getenv('DB_PASSWORD')
        aws_name = os.getenv('DB_NAME')
        aws_charset = os.getenv('DB_CHARSET', 'utf8mb4')  # Default to 'utf8mb4'
        self.awssql = thresholdSQL( aws_host, aws_port, aws_user, aws_password, aws_name, aws_charset)
        
        awsBool = os.getenv('AWSBOOL')
        self.awsState = False
        if str(awsBool).lower() == 'true':
            self.awsState = True
            
            
        mqtt_host = os.getenv('MQTT_BROKER')
        mqtt_port = int(os.getenv('MQTT_PORT', 1883)) 

        self.motorThres = motorThres
        self.commandTypes = commandTypes
        self.mqtt_broker = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = Client()
        self.topicNames = topicNames
        self.num_instances = num_instances
        self.arrayName = arrayname
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            for i in range (self.num_instances):
                motorcommand = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}/Motor/threshold"
                commandtopic = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}/controlType"
                client.subscribe(motorcommand)
                client.subscribe(commandtopic)
            print("Connected to MQTT broker")
        else:
            print("Failed to connect to MQTT broker")

    # Define the callback for message reception
    def on_message(self, client, userdata, message):
        msg = message.payload.decode("utf-8")

        for i in range (self.num_instances):
            motorcommand = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}/Motor/threshold"
            commandtopic = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}/controlType"
            # Check which topic the message belongs to
            if message.topic == motorcommand:
                motor = json.loads(msg)
                # Empty the queue first
                while not self.motorThres[i].empty():
                    self.motorThres[i].get()
                self.sql.upload(
                self.arrayName,                     # robotId
                self.topicNames[i],                 # sensorId
                datetime.datetime.now(),            # timestamp (added parentheses for the function call)
                motor['min_temp'],                  # min_temp
                motor['max_temp'],                  # max_temp
                motor['min_humidity'],              # min_humidity
                motor['max_humidity'],              # max_humidity
                motor['time_interval'],             # time_interval
                motor['duration'],                  # duration
                motor['Humidity_Var'],              # Humidity_Var
                motor['Temperature_Var'],           # Temperature_Var
                motor['autoDuration']               # autoDuration
                )
                if self.awsState:
                    self.awssql.upload(
                    self.arrayName,                     # robotId
                    self.topicNames[i],                 # sensorId
                    datetime.datetime.now(),            # timestamp (added parentheses for the function call)
                    motor['min_temp'],                  # min_temp
                    motor['max_temp'],                  # max_temp
                    motor['min_humidity'],              # min_humidity
                    motor['max_humidity'],              # max_humidity
                    motor['time_interval'],             # time_interval
                    motor['duration'],                  # duration
                    motor['Humidity_Var'],              # Humidity_Var
                    motor['Temperature_Var'],           # Temperature_Var
                    motor['autoDuration']               # autoDuration
                    )
                # Add the new motor command to the empty queue
                print(motor)
                self.motorThres[i].put(motor)

            elif message.topic == commandtopic:
                while not self.commandTypes[i].empty():
                    self.commandTypes[i].get()
                print(msg)
                self.commandTypes[i].put(msg)

    def run(self):
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to the MQTT broker and start the loop
        self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
        print(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
        

        # Start the MQTT client loop
        self.client.loop_forever()
        while True:
            time.sleep(0.1)


