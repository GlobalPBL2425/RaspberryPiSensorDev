import pymysql
from multiprocessing import Process, Queue
from typing import List
import datetime
import time

class PowerController(Process):
    def __init__(self, ip, rpiNames,powerQueueArray: List[Queue],daemon ):
        Process.__init__(self,daemon=daemon)
        self.powerQueueArray = powerQueueArray
        self.rpiNames = rpiNames
        self.motorstate = []
        self.timestamp = 0 
        self.sql = PowerSQL(ip = ip)

    def on_start(self):
        for i in range (len(self.rpiNames)):
            self.motorstate.append(0)
        self.sql.on_start()
    def run(self):
        self.on_start()
        while True:
            self.timestamp = datetime.datetime.now()
            for i , rpi in enumerate(self.rpiNames):
                if not self.powerQueueArray[i].empty():
                    self.motorstate[i] = self.powerQueueArray[i].get()
                
                self.sql.upload(rpi , self.timestamp, self.motorstate[i] )
            
            time.sleep(1)


    


class PowerSQL:
    def __init__(self, ip):
        self.conn = pymysql.connect(host= ip, 
                            port=3306, 
                            user='root', 
                            passwd='GPBL2425', 
                            db='GPBL2425', 
                            charset='utf8mb4',  
                            cursorclass=pymysql.cursors.DictCursor, 
                            autocommit=False) 
        self.cursor = self.conn.cursor()
    def on_start(self):
        #One table(ID , timestamp TIMESTAMP , motorstate/ BOOLEAN)
        powerTable = f"""CREATE TABLE IF NOT EXISTS PowerUsage (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    robotId VARCHAR(128) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    motorstate BOOLEAN
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
        sqlcommand = f"INSERT INTO PowerUsage (robotId, timestamp, motorstate) VALUES (%s, %s, %s)"
        try:
            # Execute the SQL command with parameters to avoid SQL injection
            self.cursor.execute(sqlcommand, (sensor_ID, timestamp, timestamp, motorstate))
            self.conn.commit()  # Commit the transaction
        except Exception as e:
            print(f"Error during data insertion: {e}")
            self.conn.rollback()  # Roll back the transaction in case of an error
    
    def stop(self):
        self.cursor.close()
        self.conn.close()

