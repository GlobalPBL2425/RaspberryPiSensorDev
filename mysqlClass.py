import time
import pymysql
from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json
import datetime


class ControllerPool(Process):
    def __init__(self,arrayName, sensorId, sensor_queue, interval, motorPWM, commandType,daemon):
        Process.__init__(self, daemon=daemon)
        self.slaveFunc = None
        self.sensor_queue = sensor_queue
        self.commandType = commandType
        self.motorPWM = motorPWM
        self.MYSQL = MySQL(sensor_ID=sensorId,arrayName=arrayName)
        self.interval = interval
        self.motorPWM = motorPWM

    def run(self):
        while True:
            if not self.motorPWM.empty():
                pwm = self.motorPWM.get()
            if not self.commandType.empty():
                commandType = self.commandType.get()
            if not self.sensor_queue.empty():
                sensor = self.sensor_queue.get()
            timestamp = self.get_rounded_timestamp()
            self.MYSQL.upload(timestamp=timestamp,temperature=sensor[0],humidity=sensor[1],controlMode=commandType, motorDutyCycle=pwm)



            time.sleep(3)  # Wait 3 seconds before getting the next timestamp



    def stop(self):
        self.running = False

    def get_rounded_timestamp(self):
        now = datetime.now()
        # Always round down the seconds to the nearest multiple of 3 (i.e., 0, 3, 6, 9, ...)
        rounded_seconds = (now.second // self.interval) * self.interval
        rounded_now = now.replace(second=rounded_seconds, microsecond=0)
        return rounded_now

    






class MySQL:
    def __init__(self, sensor_ID, arrayName):
        self.conn = pymysql.connect(host='172.20.10.2', 
                            port=3306, 
                            user='root', 
                            passwd='GPBL2425', 
                            db='testdb', 
                            charset='utf8mb4',  
                            cursorclass=pymysql.cursors.DictCursor, 
                            autocommit=False) 
        self.cursor = self.conn.cursor()
        self.sensor_ID = sensor_ID
        self.arrayName = arrayName
    def on_start(self):
        #One table(ID , Robot ID ,timestamp TIMESTAMP , humidity FLOAT NOT NULL, temperature FLOAT NOT NULL , (command type (auto/timer)){thersholds}, PWM of motor(%))
        readingTable = f"""CREATE TABLE IF NOT EXISTS SensorReading (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    robotId VARCHAR(128) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    temperature FLOAT NOT NULL,
                    humidity FLOAT NOT NULL,
                    controlMode VARCHAR(128) NOT NULL,
                    motorDutyCycle FLOAT 
                    )
                    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        self.cursor.execute(readingTable)
        #another table (temperature conditions (cold , hot , normal),)
        arrayTable = f"""CREATE TABLE IF NOT EXISTS Thresholds (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(128) NOT NULL,
                minTemp FLOAT NOT NULL,
                maxTemp FLOAT NOT NULL,
                minHum FLOAT NOT NULL,
                maxHum FLOAT NOT NULL
                )
                ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        
        self.cursor.execute(arrayTable)

        """
        Arraycommand = f"INSERT INTO ArrayTable (sensor_ID, array_Name) VALUES (%s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(Arraycommand, (self.sensor_ID, self.arrayName))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
        """

    def upload(self, temperature, humidity, timestamp,controlMode ,motorDutyCycle):
        sqlcommand = f"INSERT INTO SensorReading (robotId, timestamp, temperature, humidity, controlMode ,motorDutyCycle) VALUES (%s, %s, %s, %s, %s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(sqlcommand, (self.sensor_ID, timestamp, temperature, humidity, controlMode ,motorDutyCycle))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
    
    def stop(self):
        self.cursor.close()
        self.conn.close()


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


# Simulate sensor data input and motor control commands
if __name__ == "__main__":
    # Create queues for inter-process communication
    sensor_queue = Queue()
    motorPWM_queue = Queue()
    commandType_queue = Queue()

    # Create a controller pool object with test parameters
    controller = ControllerPool(
        arrayName="TestArray",
        sensorId="Sensor_001",
        sensor_queue=sensor_queue,
        interval=3,
        motorPWM=motorPWM_queue,
        commandType=commandType_queue,
        daemon=True
    )

    # Start the ControllerPool process
    controller.start()

    # Simulate incoming sensor data and command updates
    for i in range(10):
        # Simulating sensor data: (temperature, humidity)
        sensor_data = (25.0 + i, 60.0 + i)
        sensor_queue.put(sensor_data)

        # Simulating motor PWM updates
        motor_pwm_value = i * 10  # Example motor PWM duty cycle
        motorPWM_queue.put(motor_pwm_value)

        # Simulating command type updates (e.g., auto or timer control mode)
        if i % 2 == 0:
            commandType_queue.put("AUTO")
        else:
            commandType_queue.put("TIMER")

        # Sleep to simulate time intervals between readings
        time.sleep(5)

    # Stop the process after running the test
    controller.terminate()
    controller.join()

    print("Test completed.")