import boto3
from paho.mqtt.client import mqtt
import json
import time , datetim
import threading
import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from multiprocessing import Process, Queue

class ControllerPool:
    def __init__(self , master ,timing):
        self.master = master
        self.timing = timing*60
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
            print()
            

class AWSSensor:
    def __init__(self, bucket , arrayName , sensorId):
        self.s3_client = boto3.client('s3')
        self.bucket = bucket
        self.filepath = f"{arrayName}/{sensorId}"

    def upload(self , temp ,humd, timestamp):    
        jsonString = self.Jsonify(temp , humd)
        KeyName = f"{self.filepath}/{timestamp}.json"
        self.s3_client.put_object(Bucket=self.bucket, Key=KeyName, Body=jsonString, ContentType='application/json')

    @staticmethod
    def Jsonify(temp , humd):
        #used to convert data to json
        radict = {
            "temperature" : temp,
            "humidity" : humd
        }
        return json.dumps(radict)
    
class Master():
    def __init__(self , master ,timing , commandtopic, validtopics):
        self.master = master
        self.timing = timing*60
        self.iot_client = boto3.client('iot-data' , 'reagion name')
        self.readflag = 1
        self.commandTopic = commandtopic
        self.mqtt_client = AWSIoTMQTTClient("MyClientID")
        self.mqtt_client.configureEndpoint("your-endpoint.iot.region.amazonaws.com", 8883)
        self.mqtt_client.configureCredentials("root-CA.crt", "private.pem.key", "certificate.pem.crt")

        self.validTopic = validtopics
        self.timestamp = None 
        self.message = {
            "Command": "Read",
            "Timestamp": ""
        }
        self.controlFlag = False #Controls the sensor class to read or write

    def mainFunc(self):

        while True:
            self.message['Command'] = True
            self.readflag = True
            self.timestamp = datetime.datetime.now
            self.iot_client.publish(topic=self.commandTopic,
                qos=1,  # QoS level 1 ensures delivery at least once
                payload=json.dumps(self.message)
            )   
            self.acknowledgement()
    
    
            time.sleep(self.timing)
            self.readflag = False

    def on_message(self, client, userdata, message):
        topic = message.topic
        if topic in self.receivedTopics:
            print(f"Received message from {topic}: {message.payload.decode('utf-8')}")
            self.receivedTopics[topic] = True  # Mark that the topic has responded

    def acknowledgement(self):
        # Subscribe to all valid topics
        for topic in self.validTopics:
            self.mqtt_client.subscribe(topic, 1, self.on_message)

        print("Waiting for acknowledgements...")
        
        ####---revamp this part --- #####
        # Loop until all topics have responded
        while not all(self.receivedTopics.values()):
            time.sleep(0.01)  # Avoid busy-waiting; check every second

        print("All acknowledgements received.")
        # Reset the received topics for the next cycle
        self.receivedTopics = {topic: False for topic in self.validTopics}
        ####---revamp this part --- #####
        # Unsubscribe after receiving acknowledgements
        for topic in self.validTopics:
            self.mqtt_client.unsubscribe(topic)


import paho.mqtt.client as mqtt
import json

class Slave:
    def __init__(self, commandtopic, validtopic, sensorNum):
        self.readflag = 1
        self.commandTopic = commandtopic
        self.validtopic = validtopic[sensorNum]
        self.client = mqtt.Client()
        self.readflag = False

    def on_start(self):
        # Assign the on_message callback
        self.client.on_message = self.on_message

        # Connect to the MQTT broker (AWS IoT endpoint)
        self.client.connect("your-aws-iot-endpoint")

        # Subscribe to the command topic
        self.client.subscribe(self.commandTopic)

        # Start the MQTT client loop
        self.client.loop_forever()

    # Define the callback for message reception
    def on_message(self, client, userdata, message):
        command = json.loads(message.payload.decode("utf-8"))
        print("Received command:", command)
        
        if command.get("command") == True:
            print("Starting data collection...")

        elif command.get("command") == False:
            print("Stop reading data")


    
    

# Function to start data collection (placeholder)
def start_data_collection():
    # Collect data from sensors, etc.
    print("Collecting data...")

# Function to sync data to AWS S3
def sync_data_to_s3():
    # Sync collected data to S3
    print("Syncing to S3...")

# Initialize MQTT client and subscribe to the command topic
