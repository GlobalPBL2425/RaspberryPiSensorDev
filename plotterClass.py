import matplotlib.pyplot as plt
import time 

class plotterFunc:
    def __init__(self):
        self.ax1 = None

    
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


