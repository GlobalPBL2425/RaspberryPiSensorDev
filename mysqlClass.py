import time
import pymysql
from multiprocessing import Queue, Process
from paho.mqtt.client import Client
import json



class ControllerPool(Process):
    def __init__(self,arrayName, sensorId, sensor_queue, thershold_queue:Queue, daemon):
        Process.__init__(self, daemon=daemon)
        self.slaveFunc = None
        self.sensor_queue = sensor_queue
        self.thershold_queue = thershold_queue
        self.MYSQL = MySQL(sensor_ID=sensorId,arrayName=arrayName)

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






class MySQL:
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
        #One table(ID , Robot ID ,timestamp TIMESTAMP , humidity FLOAT NOT NULL, temperature FLOAT NOT NULL , (command type (auto/timer)){thersholds}, PWM of motor(%))
        readingTable = f"""CREATE TABLE IF NOT EXISTS {self.sensor_ID} (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    humidity FLOAT NOT NULL,
                    temperature FLOAT NOT NULL
                    )
                    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        self.cursor.execute(readingTable)
        #another table (temperature conditions (cold , hot , normal),)
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
