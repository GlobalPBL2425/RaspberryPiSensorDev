from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import time

class MQTTFunc(Process):
    def __init__(self, commandTopic, motorTopic, sensorqueue, mqtt_broker, motorThres : Queue,commandType: Queue, mqtt_port ,daemon):
        Process.__init__(self, daemon=daemon)
        self.motorTopic = motorTopic
        self.commandTopic = commandTopic
        self.commandType = commandType
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = Client()
        self.motorThres = motorThres
        self.sensor_queue = sensorqueue
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            # Subscribe to the command topic
            client.subscribe(self.motorTopic)
            client.subscribe(self.commandTopic)
            print("Connected to MQTT broker")
        else:
            print("Failed to connect to MQTT broker")

    # Define the callback for message reception
    def on_message(self, client, userdata, message):
        msg = message.payload.decode("utf-8")
        
        # Check which topic the message belongs to
        if message.topic == self.motorCommand:
            motor = json.loads(msg)
            if self.motorThres.empty():
                self.motorThres.put(motor)  # Add motor command to queue if empty
            else:
                self.motorThres.get()  # Replace existing value if the queue has data
                self.motorThres.put(motor)

        elif message.topic == self.commandTopic:
            if self.commandType.empty():
                self.commandType.put(msg)  # Add command type to queue if empty
            else:
                self.commandType.get()  # Replace existing value if the queue has data
                self.commandType.put(msg)

    def run(self):
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to the MQTT broker and start the loop
        self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
        print(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")

        # Start the MQTT client loop
        self.client.loop_forever()


