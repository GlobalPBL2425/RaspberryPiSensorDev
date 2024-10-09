import matplotlib.pyplot as plt 
from collections import deque

class plotterFunc:
    def __init__(self):
        self.temperature_data = deque(maxlen=50)
        self.humidity_data = deque(maxlen=50)
        self.time_data= deque(maxlen=50)
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6))

    def plotingFunc(self,temperature, humidity,current_time):
        if temperature is not None and humidity is not None:
                print(f"Temperature: {temperature:.1f} °C    Humidity: {humidity:.1f}%")
                
                # Append the new data to the deques
                self.temperature_data.append(temperature)
                self.humidity_data.append(humidity)
                self.time_data.append(current_time)
                
                # Update the plot with the new data
                self.update_plot(self.time_data,self.temperature_data,self.humidity_data)

        else:
            print("Failed to retrieve data from the sensor")




    def update_plot(self , time_data,temperature_data,humidity_data):
        # Clear the plots
        
        self.ax1.clear()
        self.ax2.clear()

        # Plot temperature data
        self.ax1.plot(time_data, temperature_data, color='r', label='Temperature (°C)')
        self.ax1.set_ylabel('Temperature (°C)')
        self.ax1.legend(loc='upper left')
        self.ax1.set_ylim([min(temperature_data) - 1, max(temperature_data) + 1])

        # Plot humidity data
        self.ax2.plot(time_data, humidity_data, color='b', label='Humidity (%)')
        self.ax2.set_ylabel('Humidity (%)')
        self.ax2.legend(loc='upper left')
        self.ax2.set_ylim([min(humidity_data) - 1, max(humidity_data) + 1])

        # Set the common X axis
        self.ax1.set_xlabel('Time (s)')
        self.ax2.set_xlabel('Time (s)')
        
        plt.tight_layout()
        plt.pause(0.1)  # Pause for a brief moment to update the plot


