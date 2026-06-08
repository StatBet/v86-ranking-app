import pandas as pd

df = pd.read_csv("ml_dataset.csv")

zero = df[df["avg_odds"] == 0]

print("=" * 80)
print("AVG_ODDS = 0")
print("=" * 80)

print(len(zero))

print(
    zero[
        [
            "date",
            "race_no",
            "horse",
            "avg_odds"
        ]
    ]
    .head(20)
    .to_string(index=False)
)