import boto3
from paho.mqtt.client import Client
import json
import time , datetime
import threading

class AWSSensor:
    def __init__(self, bucket , arrayName , sensorId):
        self.s3_client = boto3.client('s3')
        self.bucket = bucket
        self.filepath = f"{arrayName}/{sensorId}"

    def upload(self , temp ,humd, timestamp):    
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
    
class Master():
    def __init__(self , master ,timing , topic, ):
        self.master = master
        self.timing = timing*60
        self.client = boto3.client('iot-data')
        self.readflag = 1
        

    def timing(self):
        time.sleep(self.timing)
        self.readflag = True
        
    def mainFunc():



class Slave():
    
