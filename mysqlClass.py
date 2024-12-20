import time
import pymysql
from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import datetime
import threading
from dotenv import load_dotenv
import os
"""unused code 
class ControllerPool(Process):
    def __init__(self,arrayName, sensorId, sensor_queue, interval, motorPWM, commandType, ip,daemon):
        Process.__init__(self, daemon=daemon)
        self.slaveFunc = None
        self.sensor_queue = sensor_queue
        self.commandType = commandType
        self.motorPWM = motorPWM
        self.MYSQL = None
        self.sensorId = sensorId
        self.arrayName = arrayName
        self.interval = interval
        self.motorPWM = motorPWM
        self.ip = ip
        self.pwm = 10
        self.command= 'auto'
        self.sensor = None


    def run(self):
        self.MYSQL = MySQL(sensor_ID=self.sensorId,arrayName=self.arrayName , ip= self.ip)
        self.MYSQL.on_start()
        try:
            while True:
                if not self.motorPWM.empty():
                    self.pwm = self.motorPWM.get()
                if not self.commandType.empty():
                    self.command = self.commandType.get()
                if not self.sensor_queue.empty():
                    self.sensor = self.sensor_queue.get()
                
                if self.sensor and self.pwm and self.command is not None:
                    timestamp = self.get_rounded_timestamp()
                    self.MYSQL.upload(sensor_ID=self.sensor[4],timestamp=self.sensor[2],temperature=self.sensor[0],humidity=self.sensor[1],controlMode=self.commandType, motorDutyCycle=self.pwm)

                time.sleep(self.interval)  # Wait 3 seconds before getting the next timestamp
        finally:
            # Ensure the MySQL connection is closed when the process stops
            self.MYSQL.stop()

    def stop(self):
        self.running = False

    def get_rounded_timestamp(self):
        now = datetime.datetime.now()
        # Always round down the seconds to the nearest multiple of 3 (i.e., 0, 3, 6, 9, ...)
        rounded_seconds = (now.second // self.interval) * self.interval
        rounded_now = now.replace(second=rounded_seconds, microsecond=0)
        return rounded_now
 """   
class Controller:
    def __init__(self, arrayName, sensorId, interval , db_host ,db_port):
        self.sensorId = sensorId
        self.arrayName = arrayName
        self.interval = interval
        self.pwm = 10
        self.command = 'timer'
        self.MYSQL = MySQL(sensor_ID=self.sensorId, arrayName=self.arrayName , db_host= db_host ,db_port= db_port)
    def upload(self,sensor,commandType,motorPWM):
        if not motorPWM.empty():
            self.pwm =motorPWM.get()
        if not commandType.empty():
            self.command = commandType.get()
               
        if sensor and self.pwm and self.command is not None:
            timestamp = self.get_rounded_timestamp()
            self.MYSQL.upload(robotId=self.arrayName,sensor_ID=sensor[3],timestamp=sensor[2],temperature=sensor[0],humidity=sensor[1],controlMode=self.command, motorInterval=self.pwm)
                
            #time.sleep(self.interval)  # Wait 3 seconds before getting the next timestamp

    def stop(self):
        self.running = False
    def get_rounded_timestamp(self):
        now = datetime.datetime.now()
        # Always round down the seconds to the nearest multiple of 3 (i.e., 0, 3, 6, 9, ...)
        rounded_seconds = (now.second // self.interval) * self.interval
        rounded_now = now.replace(second=rounded_seconds, microsecond=0)
        return rounded_now

class MySQL:
    def __init__(self, sensor_ID, arrayName, db_host, db_port):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        self.db_charset = os.getenv('DB_CHARSET', 'utf8mb4')  # Default to 'utf8mb4'

        self.sensor_ID = sensor_ID
        self.arrayName = arrayName
        self.conn = None
        self.cursor = None
        self.connect()
        self.on_start()

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.conn = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                passwd=self.db_password,
                db=self.db_name,
                charset=self.db_charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            self.cursor = self.conn.cursor()
            print("Database connection established.")
        except Exception as e:
            print(f"Failed to connect to database: {e}")

    def reconnect(self):
        """Re-establish the connection if it is lost."""
        if self.conn is None or not self.conn.open:
            print("Reconnecting to the database...")
            self.connect()

    def on_start(self):
        """Initialize required database structures."""
        try:
            reading_table = f"""CREATE TABLE IF NOT EXISTS SensorReading (
                        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        robotId VARCHAR(128) NOT NULL,
                        sensorId VARCHAR(128) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        temperature FLOAT NOT NULL,
                        humidity FLOAT NOT NULL,
                        controlMode VARCHAR(128) NOT NULL,
                        motorInterval FLOAT
                        )
                        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
            self.cursor.execute(reading_table)
        except Exception as e:
            print(f"Error during table creation: {e}")
            self.reconnect()

    def upload(self, robotId, sensor_ID, temperature, humidity, timestamp, controlMode, motorInterval):
        """Upload data to the database."""
        self.reconnect()
        sqlcommand = f"""INSERT INTO SensorReading 
                         (robotId, sensorId, timestamp, temperature, humidity, controlMode, motorInterval) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        try:
            self.cursor.execute(sqlcommand, (robotId, sensor_ID, timestamp, temperature, humidity, controlMode, motorInterval))
            self.conn.commit()
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()
            self.reconnect()

    def stop(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")




class thresholdSQL:
    def __init__(self, db_host, db_port, db_user, db_password, db_name, db_charset):
        self.conn = pymysql.connect(host= db_host, 
                            port=db_port, 
                            user=db_user, 
                            passwd=db_password, 
                            db=db_name, 
                            charset=db_charset,  
                            cursorclass=pymysql.cursors.DictCursor, 
                            autocommit=False) 
        self.cursor = self.conn.cursor()
        arrayTable = f"""CREATE TABLE IF NOT EXISTS Thresholds (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                robotId VARCHAR(128) NOT NULL,
                sensorId VARCHAR(128) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                min_temp FLOAT NOT NULL,
                max_temp FLOAT NOT NULL,
                min_humidity FLOAT NOT NULL,
                max_humidity FLOAT NOT NULL,
                time_interval FLOAT NOT NULL,
                duration FLOAT NOT NULL,
                Humidity_Var FLOAT NOT NULL,
                Temperature_Var FLOAT NOT NULL,
                autoDuration FLOAT NOT NULL
                )
                ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        self.cursor.execute(arrayTable)

    def upload(self, robotId,sensorId,timestamp,min_temp,max_temp,min_humidity,max_humidity,time_interval,duration,Humidity_Var,Temperature_Var,autoDuration):
        sqlcommand = f"INSERT INTO SensorReading (robotId,sensorId,timestamp,min_temp,max_temp,min_humidity,max_humidity,time_interval,duration,Humidity_Var,Temperature_Var,autoDuration):VALUES (%s,%s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(sqlcommand, (robotId,sensorId,timestamp,min_temp,max_temp,min_humidity,max_humidity,time_interval,duration,Humidity_Var,Temperature_Var,autoDuration))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
    



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

'''
# Simulate sensor data input and motor control commands
if __name__ == "__main__":
    # Create queues for inter-process communication
    sensor_queue = Queue()
    motorPWM_queue = Queue()
    commandType_queue = Queue()
    motorThres =Queue()

    # Create a ControllerPool object with test parameters
    controller = ControllerPool(
        sensorId="Sensor_001",           # Simulated sensor ID
        arrayName= "Group1",
        sensor_queue=sensor_queue,       # Queue for sensor data
        interval=3,                      # Interval for timestamp rounding
        motorPWM=motorPWM_queue,         # Queue for motor PWM control
        commandType=commandType_queue,   # Queue for control type (AUTO/TIMER)
        daemon=True                      # Run the process as a daemon
    )

    # Start the ControllerPool process
    controller.start()

    # Simulate incoming sensor data and command updates for testing
    for i in range(10):
        # Simulating sensor data: (temperature, humidity)
        sensor_data = (25.0 + i, 60.0 + i)
        sensor_queue.put(sensor_data)  # Put sensor data into the queue

        # Simulating motor PWM updates
        motor_pwm_value = i * 10  # Example motor PWM duty cycle
        motorPWM_queue.put(motor_pwm_value)  # Put PWM value into the queue

        # Simulating control mode updates (e.g., AUTO or TIMER control mode)
        if i % 2 == 0:
            commandType_queue.put("AUTO")  # AUTO mode
        else:
            commandType_queue.put("TIMER")  # TIMER mode

        # Sleep to simulate time intervals between readings
        time.sleep(5)

    # After the simulation, stop the ControllerPool process
    controller.terminate()
    controller.join()

    print("ControllerPool test completed.")
    '''