import boto3
from paho.mqtt.client import Client
import json
import time , datetim
import threading
import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

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




class Slave():
    def __init__(self):
        self.readflag = 1