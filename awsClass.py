import boto3
from paho.mqtt.client import Client
import json
import time , datetime
import threading
import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from multiprocessing import Process, Queue


class ControllerPool(Process):
    def __init__(self, master, timing, daemon, bucket, arrayName, sensorId, sensor_queue, thershold_queue:Queue):
        Process.__init__(self, daemon=daemon)
        self.master = master
        self.timing = timing*60
        self.masterFunc = None
        self.slaveFunc = None
        self.sensor_queue = sensor_queue
        self.AWS = AWSSensor(bucket , arrayName , sensorId)
        self.thershold_queue = thershold_queue
        # to be change
        self.slaveFunc = Slave(AWS=self.AWS, commandTopic="sensor/command", validtopic=["sensor/valid"], 
                            motorCommand="sensor/motor", sensorNum=0, sensorqueue=self.sensor_queue)
        def run(self):
        # Initialize SlaveFunc here
           
            
            # Start SlaveFunc in a separate thread to handle MQTT communication
            slave_thread = threading.Thread(target=self.slaveFunc.on_start)
            slave_thread.start()

            # Main loop to handle processing
            while self.running:
                self.slaveFunc  # Initialize if not done already
                if self.thershold_queue.empty():
                    # Check if motor threshold from Slave is ready
                    if self.slaveFunc.motorThres is not None:
                        self.thershold_queue.put(self.slaveFunc.motorThres)
                time.sleep(1)  # Avoid tight looping, add some delay

    def stop(self):
        self.running = False

class AWSSensor:
    def __init__(self, bucket, arrayName, sensorId):
        self.s3_client = boto3.client('s3')
        self.bucket = bucket
        self.filepath = f"{arrayName}/{sensorId}"

    def upload(self, temp, humd, timestamp):    
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




class Slave:
    def __init__(self, AWS,  commandTopic, validtopic, motorCommand, sensorNum, sensorqueue):
        self.readflag = 1
        self.commandTopic = commandTopic
        self.motorCommand = motorCommand
        self.validtopic = validtopic[sensorNum]
        self.client = Client()
        self.readflag = False
        self.motorThres = None
        self.AWS = AWS
        self.sensor_queue = sensorqueue
 

    def on_start(self):
        # Assign the on_message callback
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to the MQTT broker (AWS IoT endpoint)
        self.client.connect("your-aws-iot-endpoint")

        # Subscribe to the command topic
        self.client.subscribe(self.commandTopic)

        # Start the MQTT client loop
        self.client.loop_forever()
    
    def on_connect(self,client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            client.subscribe(self.commandTopic)
            client.subscribe(self.motorCommand)
        else:
            print("Failed to connect to MQTT broker")

    # Define the callback for message reception
    def on_message(self, client, userdata, message):
        msg = message.payload.decode("utf-8")    
        if msg.topic == self.commandTopic:
            command = json.loads(msg)
            print("Received command:", command)

            if command.get("command") == True:
                print("Starting data collection...")
                self.AWS.upload(temp=self.sensor_queue[0], humd=self.sensor_queue[1], timestamp= command.get("timestamp"))
                self.client.publish(self.validtopic, "Data published", 0)

            elif command.get("command") == False:
                print("Stop reading data")
        elif msg.topic == self.motorCommand:
            motor = json.loads(msg)
            self.motorThres = motor

    def run(self):
        time.sleep(0.5)









"""
class Master():
    def __init__(self , master ,timing , commandtopic, motorCommand, validtopics):
        self.master = master
        self.timing = timing*60
        self.iot_client = boto3.client('iot-data' , 'reagion name')
        self.readflag = 1
        self.commandTopic = commandtopic
        self.mqtt_client = AWSIoTMQTTClient("MyClientID")
        self.mqtt_client.configureEndpoint("your-endpoint.iot.region.amazonaws.com", 8883)
        self.mqtt_client.configureCredentials("root-CA.crt", "private.pem.key", "certificate.pem.crt")
        self.motorCommand = motorCommand
        self.validTopic = validtopics
        self.timestamp = None 
        self.message = {
            "Command": "Read",
            "Timestamp": ""
        }
        self.controlFlag = False #Controls the sensor class to read or write

    def mainFunc(self):
        self.message['Command'] = True
        self.readflag = True
        self.timestamp = datetime.datetime.now
        self.iot_client.publish(topic=self.commandTopic,
            qos=1,  # QoS level 1 ensures delivery at least once
            payload=json.dumps(self.message)
        )   
        self.iot_client.publish(topic=self.validTopic[0],
            qos=1,  # QoS level 1 ensures delivery at least once
            payload=True
        )   
        
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
        self.mqtt_client.subscribe(self.motorCommand, 1, self.on_message)
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
"""