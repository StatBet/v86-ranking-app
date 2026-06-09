import pandas as pd

df = pd.read_csv("ml_dataset.csv")

zero = df[df["avg_odds"] == 0]

print("=" * 80)
print("AVG_ODDS = 0")
print("=" * 80)

print("Antal:", len(zero))

print()
print(
    zero[
        [
            "horse",
            "starts",
            "wins",
            "avg_odds",
            "win_percent",
            "place_percent"
        ]
    ]
    .head(50)
    .to_string(index=False)
)

print()
print("Starter-fördelning")

print(
    zero["starts"]
    .value_counts()
    .sort_index()
    .to_string()
)