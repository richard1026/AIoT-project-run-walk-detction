import pandas as pd
import time
import json
import joblib
import paho.mqtt.client as mqtt

# =========================
# 基本設定
# =========================
DATASET_PATH = "stream_data.csv"
MODEL_PATH = "model.pkl"

THINGSBOARD_HOST = "127.0.0.1"
THINGSBOARD_PORT = 1883
ACCESS_TOKEN = "jtqHiMXgcNh8JrvbARCz"

# 每筆資料間隔幾秒
SEND_INTERVAL = 1

# 每跑完一次 dataset 後，休息幾秒再重頭送
LOOP_REST_INTERVAL = 3

# activity 數字轉文字
# 如果你發現 walk/run 相反，就把 0 和 1 對調
ACTIVITY_MAP = {
    0: "walk",
    1: "run"
}

# =========================
# Dataset 欄位設定
# =========================
feature_cols = [
    "acceleration_x",
    "acceleration_y",
    "acceleration_z",
    "gyro_x",
    "gyro_y",
    "gyro_z"
]

target_col = "activity"


# =========================
# 工具函式
# =========================
def activity_to_text(value):
    """將 activity 的 0/1 轉成 walk/run；如果不是 0/1 就維持原文字。"""
    try:
        return ACTIVITY_MAP.get(int(value), str(value))
    except (ValueError, TypeError):
        return str(value)


# =========================
# 讀取 dataset 和 ML model
# =========================
print("正在載入 dataset.csv ...")
df = pd.read_csv(DATASET_PATH)

print("正在載入 model.pkl ...")
model = joblib.load(MODEL_PATH)

print("資料欄位：")
print(df.columns)

# 檢查必要欄位是否存在
missing_cols = []
for col in feature_cols:
    if col not in df.columns:
        missing_cols.append(col)

if target_col not in df.columns:
    missing_cols.append(target_col)

if missing_cols:
    print("缺少以下欄位：")
    print(missing_cols)
    exit()

print(" Dataset 欄位檢查完成")
print(f"Dataset 總筆數：{len(df)}")


# =========================
# MQTT 連線 ThingsBoard
# =========================
print("正在連線到 ThingsBoard MQTT ...")

client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)

try:
    client.connect(THINGSBOARD_HOST, THINGSBOARD_PORT, 60)
    client.loop_start()
    print("MQTT 已連線 ThingsBoard")
except Exception as e:
    print(" MQTT 連線失敗")
    print(e)
    exit()


# =========================
# 無限循環模擬感測器送資料
# =========================
print("開始無限循環傳送感測器資料與 ML 預測結果 ...")
print("若要停止，請按 Ctrl + C")

total_count = 0
correct_count = 0
loop_count = 0

try:
    while True:
        loop_count += 1
        print(f"\n========== 第 {loop_count} 輪 dataset streaming 開始 ==========")

        for index, row in df.iterrows():
            # 取出一筆 sensor feature
            X = pd.DataFrame([[row[col] for col in feature_cols]], columns=feature_cols)

            # 模型預測，原始結果可能是 0/1
            predicted_raw = model.predict(X)[0]
            actual_raw = row[target_col]

            # 轉成 walk/run 文字
            predicted_activity = activity_to_text(predicted_raw)
            actual_activity = activity_to_text(actual_raw)

            # 是否預測正確：用原始值比較比較準
            correct = int(predicted_raw == actual_raw)

            total_count += 1
            correct_count += correct
            current_accuracy = correct_count / total_count

            payload = {
                "acc_x": float(row["acceleration_x"]),
                "acc_y": float(row["acceleration_y"]),
                "acc_z": float(row["acceleration_z"]),
                "gyro_x": float(row["gyro_x"]),
                "gyro_y": float(row["gyro_y"]),
                "gyro_z": float(row["gyro_z"]),

                # 文字版：給 Dashboard 顯示
                "actual_activity": actual_activity,
                "predicted_activity": predicted_activity,

                # 原始數字：方便除錯或報告
                "actual_activity_raw": int(actual_raw),
                "predicted_activity_raw": int(predicted_raw),

                "correct": correct,
                "current_accuracy": round(current_accuracy, 4),
                "stream_loop": loop_count,
                "stream_index": int(index),
                "total_sent": total_count
            }

            result = client.publish("v1/devices/me/telemetry", json.dumps(payload))
            result.wait_for_publish()

            print(f"第 {total_count} 筆已送出：predicted={predicted_activity}, actual={actual_activity}, accuracy={round(current_accuracy, 4)}")
            time.sleep(SEND_INTERVAL)

        print(f"========== 第 {loop_count} 輪 dataset streaming 結束，{LOOP_REST_INTERVAL} 秒後重頭開始 ==========")
        time.sleep(LOOP_REST_INTERVAL)

except KeyboardInterrupt:
    print("\n收到 Ctrl + C，停止無限循環傳送")

finally:
    client.loop_stop()
    client.disconnect()
    print("✅ MQTT 已中斷連線")
    print(f"總送出筆數：{total_count}")
    print(f"正確筆數：{correct_count}")
    if total_count > 0:
        print(f"累積準確率：{round(correct_count / total_count, 4)}")