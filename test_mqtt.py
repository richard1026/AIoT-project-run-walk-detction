import json
import time
import paho.mqtt.client as mqtt

THINGSBOARD_HOST = "127.0.0.1"
ACCESS_TOKEN = "jtqHiMXgcNh8JrvbARCz"

client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)

# ✅ 連線
client.connect(THINGSBOARD_HOST, 1883, 60)

# ✅ 啟動背景 loop（很重要）
client.loop_start()

payload = {
    "acc_x": 0.12,
    "acc_y": -0.35,
    "acc_z": 9.71,
    "gyro_x": 0.01,
    "gyro_y": -0.03,
    "gyro_z": 0.05,
    "prediction": "walk"
}

# ✅ 發送
client.publish("v1/devices/me/telemetry", json.dumps(payload))

print("已送出 MQTT 資料")

# ✅ 等一下 (給時間送出去)
time.sleep(2)

# ✅ 關閉
