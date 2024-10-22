from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import time

class MQTTFunc(Process):
    def __init__(self, mySQLFunc, motorCommand, sensorqueue, mqtt_broker, motorThres : Queue, mqtt_port ,daemon):
        Process.__init__(self, daemon=daemon)
        self.readflag = 1
        self.motorCommand = motorCommand
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = Client()
        self.motorThres = motorThres
        self.sensor_queue = sensorqueue
 

    def start(self):
        # Assign the on_message callback
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to the MQTT broker (actuall mqtt)
        self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)

        # Start the MQTT client loop
        self.client.loop_forever()
    
    def on_connect(self,client, userdata, flags, rc):
        if rc == 0:
            # Subscribe to the command topic
            client.subscribe(self.motorCommand)
            print("Connected to MQTT broker")
        else:
            print("Failed to connect to MQTT broker")

    # Define the callback for message reception
    def on_message(self, client, userdata, message):
        msg = message.payload.decode("utf-8")    
        
        if msg.topic == self.motorCommand:
            motor = json.loads(msg)
            self.motorThres = motor
            if self.motorThres.empty():
                self.motorThres.put(motor)


    def run(self):
        while True:
            time.sleep(0.5)


