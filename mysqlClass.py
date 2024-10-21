import time
import pymysql
from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json


"""
MQTT INFO 
# MQTT
mqtt_broker = "127.0.0.1"
mqtt_port = 1883
topics
arrayName = "SensorArray_1"
sensorId = "Rpi-sensor_01" 
"""


class ControllerPool(Process):
    def __init__(self,arrayName, sensorId, sensor_queue, thershold_queue:Queue, daemon):
        Process.__init__(self, daemon=daemon)
        Process.__init__(self, daemon=daemon)
        self.slaveFunc = None
        self.sensor_queue = sensor_queue
        self.thershold_queue = thershold_queue
        # to be change
        self.slaveFunc = MQTTFunc()
class MySQLPool:
    def __init__(self, sensor_queue, sensor_ID, arrayName):
        self.conn = pymysql.connect(host='172.20.10.2', 
                            port=3306, 
                            user='root', 
                            passwd='GPBL2425', 
                            db='testdb', 
                            charset='utf8mb4',  
                            cursorclass=pymysql.cursors.DictCursor, 
                            autocommit=False) 
        self.cursor = self.conn.cursor()
        self.sensor_queue = sensor_queue
        self.sensor_ID = sensor_ID
        self.arrayName = arrayName
    def on_start(self):
        readingTable = f"""CREATE TABLE IF NOT EXISTS {self.sensor_ID} (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    humidity FLOAT NOT NULL,
                    temperature FLOAT NOT NULL
                    )
                    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        self.cursor.execute(readingTable)
        arrayTable = f"""CREATE TABLE IF NOT EXISTS ArrayTable (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                sensor_ID VARCHAR(128) NOT NULL,
                array_Name VARCHAR(128) NOT NULL)
               ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        
        self.cursor.execute(arrayTable)
        Arraycommand = f"INSERT INTO ArrayTable (sensor_ID, array_Name) VALUES (%s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(Arraycommand, (self.sensor_ID, self.arrayName))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error


    def upload(self, temperature, humidity, timestamp):
        sqlcommand = f"INSERT INTO {self.sensor_ID} (timestamp, humidity, temperature) VALUES (%s, %s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(sqlcommand, (timestamp, humidity, temperature))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
    
    def stop(self):
        self.cursor.close()
        self.conn.close()

class MQTTFunc:
    def __init__(self, mySQLFunc, commandTopic, validtopic, motorCommand, sensorNum, sensorqueue, mqtt_broker, mqtt_port):
        self.readflag = 1
        self.commandTopic = commandTopic
        self.motorCommand = motorCommand
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.validtopic = validtopic[sensorNum]
        self.client = Client()
        self.readflag = False
        self.motorThres = None
        self.mySQLFunc = mySQLFunc
        self.sensor_queue = sensorqueue
 

    def on_start(self):
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
                self.mySQLFunc.upload(temp=self.sensor_queue[0], humd=self.sensor_queue[1], timestamp= command.get("timestamp"))
                self.client.publish(self.validtopic, "Data published", 0)

            elif command.get("command") == False:
                print("Stop reading data")
        elif msg.topic == self.motorCommand:
            motor = json.loads(msg)
            self.motorThres = motor

    def run(self):
        time.sleep(0.5)

"""

# データをインサート                
cursor.execute("INSERT INTO test VALUES (1, 'AAA')")
cursor.execute("INSERT INTO test VALUES (2, 'BBB')")
cursor.execute("INSERT INTO test VALUES (3, 'CCC')")
cursor.execute("INSERT INTO test VALUES (4, 'DDD')")

# データを更新
cursor.execute('UPDATE test SET name=%s WHERE id=%s', ('BBBupdate', 2))

# データを削除
cursor.execute('DELETE FROM test WHERE id=3')

# データベースに反映
conn.commit()

# データを取得
cursor.execute('SELECT * FROM test')
fetch = cursor.fetchall()

print(fetch)

cursor.close()
conn.close()
"""