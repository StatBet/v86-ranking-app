import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)
winners = df[df["won"] == 1].copy()

print("=" * 80)
print("AVG_ODDS FORMATKONTROLL")
print("=" * 80)

print(winners["avg_odds"].describe().round(2).to_string())

print()
print("=" * 80)
print("20 LÄGSTA AVG_ODDS VINNARE")
print("=" * 80)

print(
    winners.sort_values("avg_odds")
    [["date", "race_no", "horse", "model_rank", "avg_odds"]]
    .head(20)
    .to_string(index=False)
)

print()
print("=" * 80)
print("20 HÖGSTA AVG_ODDS VINNARE")
print("=" * 80)

print(
    winners.sort_values("avg_odds", ascending=False)
    [["date", "race_no", "horse", "model_rank", "avg_odds"]]
    .head(20)
    .to_string(index=False)
)