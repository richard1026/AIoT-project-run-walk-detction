import pandas as pd

df = pd.read_csv("dataset.csv")

# 依資料原本時間順序切分
split_idx = int(len(df) * 0.8)

train_df = df.iloc[:split_idx]
stream_df = df.iloc[split_idx:]

train_df.to_csv("train_data.csv", index=False)
stream_df.to_csv("stream_data.csv", index=False)

print("切分完成")
print("train_data.csv:", train_df.shape)
print("stream_data.csv:", stream_df.shape)

print("Train activity distribution:")
print(train_df["activity"].value_counts())

print("Stream activity distribution:")
print(stream_df["activity"].value_counts())