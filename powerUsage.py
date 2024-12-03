import pymysql
from multiprocessing import Process, Queue
from typing import List
import datetime
import time
from dotenv import load_dotenv
import os

class PowerController(Process):
    def __init__(self, arrayname , rpiNames, powerQueueArray : List[Queue],daemon ):
        Process.__init__(self,daemon=daemon)
        self.powerQueueArray = powerQueueArray
        self.rpiNames = rpiNames
        self.motorstate = []
        self.interval = 1 
        self.sql = PowerSQL( arrayname=arrayname)

    def on_start(self):
        for i in range (len(self.rpiNames)):
            self.motorstate.append(0)
        self.sql.on_start()
    def run(self):
        self.on_start()
        while True:
            timestamp = self.get_rounded_timestamp()
            for i , rpi in enumerate(self.rpiNames):
                if not self.powerQueueArray[i].empty():
                    self.motorstate[i] = self.powerQueueArray[i].get()
                
                self.sql.upload(rpi , timestamp, self.motorstate[i] )
            
            time.sleep(1)

    def get_rounded_timestamp(self):
        now = datetime.datetime.now()
        # Round down the seconds to the nearest multiple of interval
        rounded_seconds = (now.second // self.interval) *self.interval
        rounded_now = now.replace(second=rounded_seconds, microsecond=0)
        return rounded_now





    


class PowerSQL:
    def __init__(self, arrayname):
        load_dotenv()

        # Retrieve database credentials from environment variables
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT', 3306))  # Use default port 3306 if not specified
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        db_charset = os.getenv('DB_CHARSET', 'utf8mb4')  # Default to 'utf8mb4'
        
        self.conn = pymysql.connect(host= db_host, 
                            port=db_port, 
                            user=db_user, 
                            passwd=db_password, 
                            db=db_name, 
                            charset=db_charset,  
                            cursorclass=pymysql.cursors.DictCursor, 
                            autocommit=False) 
        self.cursor = self.conn.cursor()
        
        self.arrayname = arrayname
    def on_start(self):
        #One table(ID , timestamp TIMESTAMP , motorstate/ BOOLEAN)
        powerTable = f"""CREATE TABLE IF NOT EXISTS PowerUsage (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    robotId VARCHAR(128) NOT NULL,
                    sensorId VARCHAR(128) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    motorstate INT NOT NULL
                    )
                    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
        self.cursor.execute(powerTable)

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

    def upload(self,sensor_ID , timestamp, motorstate):
        sqlcommand = f"INSERT INTO PowerUsage (robotId, sensorId, timestamp, motorstate) VALUES (%s, %s, %s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(sqlcommand, (self.arrayname ,sensor_ID, timestamp, motorstate))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
    
    def stop(self):
        self.cursor.close()
        self.conn.close()

