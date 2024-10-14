import time
import board
import adafruit_dht
import matplotlib.pyplot as plt
from collections import deque
import csv , os
import datetime


# GPIO 16に接続されたDHT22センサーを初期化 - Initialize the DHT22 sensor connected to GPIO 16
dht_device = adafruit_dht.DHT22(board.D16)

#温度と湿度のデータを保存するデック（固定長のリスト）を作成 Create deques to store temperature and humidity readings
temperature_data = deque(maxlen=50)  # 最後の50回分の温度データを保存 - Stores the last 50 temperature readings
humidity_data = deque(maxlen=50)     # 最後の50回分の湿度データを保存 - Stores the last 50 humidity readings
time_data = deque(maxlen=50)         # 対応する時間データを保存 - Stores the corresponding time values

# プロットの設定 - Set up the plot
plt.ion()  # インタラクティブモードをオンにする - Turn on interactive mode
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

# CSVファイルのパスを初期化 - Initialize the csv file path
csv_file = "dht22_readings.csv"

# グラフの更新関数 -Function to update the plot
def update_plot():  
    #グラフをクリア Clear the plots
    ax1.clear()
    ax2.clear()

    # 温度データをプロット - Plot temperature data
    ax1.plot(time_data, temperature_data, color='r', label='Temperature (°C)')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend(loc='upper left')
    ax1.set_ylim([min(temperature_data) - 1, max(temperature_data) + 1])

    # 湿度データをプロット Plot humidity data
    ax2.plot(time_data, humidity_data, color='b', label='Humidity (%)')
    ax2.set_ylabel('Humidity (%)')
    ax2.legend(loc='upper left')
    ax2.set_ylim([min(humidity_data) - 1, max(humidity_data) + 1])

    #共通のX軸を設定 Set the common X axis
    ax1.set_xlabel('Time (s)')
    ax2.set_xlabel('Time (s)')
    
    plt.tight_layout()
    plt.pause(0.1)  #少し待ってプロットを更新 Pause for a brief moment to update the plot

start_time = time.time()


with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Temperature (°C)", "Humidity (%)"])

    while True:
        try:
            #センサーから温度と湿度を読み取る - Read temperature and humidity from the sensor
            temperature = dht_device.temperature
            humidity = dht_device.humidity

            #現在時刻を取得 - Get the current time
            current_time = datetime.datetime.now()  # Calculate time elapsed
            writer.writerow([current_time, temperature, humidity])

            if temperature is not None and humidity is not None:
                print(f"Temperature: {temperature:.1f} °C    Humidity: {humidity:.1f}%")
                
                #新しいデータをデックに追加 - Append the new data to the deques
                temperature_data.append(temperature)
                humidity_data.append(humidity)
                time_data.append(current_time)
                
                #新しいデータでグラフを更新 - Update the plot with the new data
                update_plot()

            else:
                print("Failed to retrieve data from the sensor")

        except RuntimeError as error:
            print(f"Error: {error.args[0]}")
            time.sleep(2.0)
            continue

        except Exception as error:
            dht_device.exit()
            raise error

        # 次の読み取りまで待機 - Wait before taking the next reading
        time.sleep(2.0)
