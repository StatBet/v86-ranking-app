import pandas as pd

df = pd.read_csv("ml_dataset.csv")

zero = df[df["avg_odds"] == 0].copy()

print("=" * 80)
print("ZERO ODDS SUMMARY")
print("=" * 80)

print("Antal rader:", len(zero))
print("Antal vinnare:", int(zero["won"].sum()))

print()
print("Start_type:")
print(zero["start_type"].value_counts().to_string())

print()
print("Distance:")
print(zero["distance"].value_counts().sort_index().to_string())

print()
print("Model rank:")
print(zero["model_rank"].value_counts().sort_index().to_string())

print()
print("Vinnare med avg_odds = 0:")
print(
    zero[zero["won"] == 1][
        ["date", "race_no", "horse", "model_rank", "starts", "win_percent", "place_percent"]
    ].to_string(index=False)
)