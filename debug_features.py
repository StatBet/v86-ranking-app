import pandas as pd

df = pd.read_csv("ml_dataset.csv")

cols = [
    "speed_score",
    "record_score",
    "form_score",
    "latest_start_score",
    "prize_money",
    "recent_prize_score",
    "class_change_score",
    "avg_time",
    "avg_odds"
]

print(df[cols].describe().T)