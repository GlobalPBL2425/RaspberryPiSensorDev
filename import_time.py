import time
import board
import adafruit_dht
import matplotlib.pyplot as plt
from collections import deque
import csv , os
import datetime


# Initialize the DHT22 sensor connected to GPIO 16
dht_device = adafruit_dht.DHT22(board.D16)

# Initialize the csv file path

# Create deques to store temperature and humidity readings
temperature_data = deque(maxlen=50)  # Stores the last 50 temperature readings
humidity_data = deque(maxlen=50)     # Stores the last 50 humidity readings
time_data = deque(maxlen=50)         # Stores the corresponding time values

# Set up the plot
plt.ion()  # Turn on interactive mode
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

# Initialize the csv file path
csv_file = "dht22_readings.csv"

def update_plot():
    # Clear the plots
    ax1.clear()
    ax2.clear()

    # Plot temperature data
    ax1.plot(time_data, temperature_data, color='r', label='Temperature (°C)')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend(loc='upper left')
    ax1.set_ylim([min(temperature_data) - 1, max(temperature_data) + 1])

    # Plot humidity data
    ax2.plot(time_data, humidity_data, color='b', label='Humidity (%)')
    ax2.set_ylabel('Humidity (%)')
    ax2.legend(loc='upper left')
    ax2.set_ylim([min(humidity_data) - 1, max(humidity_data) + 1])

    # Set the common X axis
    ax1.set_xlabel('Time (s)')
    ax2.set_xlabel('Time (s)')
    
    plt.tight_layout()
    plt.pause(0.1)  # Pause for a brief moment to update the plot

start_time = time.time()


with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Temperature (°C)", "Humidity (%)"])

    while True:
        try:
            # Read temperature and humidity from the sensor
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            current_time = datetime.datetime.now()  # Calculate time elapsed
            writer.writerow([current_time, temperature, humidity])

            if temperature is not None and humidity is not None:
                print(f"Temperature: {temperature:.1f} °C    Humidity: {humidity:.1f}%")
                
                # Append the new data to the deques
                temperature_data.append(temperature)
                humidity_data.append(humidity)
                time_data.append(current_time)
                
                # Update the plot with the new data
                update_plot()

            else:
                print("Failed to retrieve data from the sensor")

        except RuntimeError as error:
            # Errors happen occasionally, just try again
            print(f"Error: {error.args[0]}")
            time.sleep(2.0)
            continue

        except Exception as error:
            dht_device.exit()
            raise error

        # Wait before taking the next reading
        time.sleep(2.0)
