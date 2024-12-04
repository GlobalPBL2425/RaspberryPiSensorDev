from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import time
from dotenv import load_dotenv
import os

class MQTTFunc(Process):
    def __init__(self, num_instances, arrayname, motorThres : list[Queue], commandTypes: list[Queue], topicNames ,daemon):
        Process.__init__(self, daemon=daemon)
        load_dotenv()
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
                commandtopic = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}controlType"
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
            commandtopic = f"GPBL2425/{self.arrayName}/{self.topicNames[i]}controlType"
            # Check which topic the message belongs to
            if message.topic == motorcommand:
                motor = json.loads(msg)
                # Empty the queue first
                while not self.motorThres[i].empty():
                    self.motorThres[i].get()
                
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


