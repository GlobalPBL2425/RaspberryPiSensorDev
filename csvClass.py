import csv
import datetime
from multiprocessing import Process , Queue

class csvPool():
    def __init__(self, filepath):
        self.filepath = filepath

    def writeLine(self,temperature,humidity, formatted_time):
        try:
            writer = csv.writer(self.filepath)
            
            writer.writerow(formatted_time , temperature , humidity)
        except Exception as error:
            print(f"Error: {error.args}")


    def writeToCSV(self, data):
        with open(self.filepath, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(data)
            file.flush()  # Ensures data is written immediately