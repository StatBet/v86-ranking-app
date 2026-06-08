import pandas as pd

df = pd.read_csv("ml_dataset.csv")

extreme = df[df["avg_odds"] > 100].sort_values("avg_odds", ascending=False)

print("=" * 80)
print("EXTREMA AVG_ODDS > 100")
print("=" * 80)

print(
    extreme[
        ["date", "race_no", "horse", "model_rank", "avg_odds", "starts", "win_percent", "place_percent"]
    ].to_string(index=False)
)

for _, row in extreme.head(10).iterrows():
    print()
    print("=" * 80)
    print(row["date"], "Avd", row["race_no"], row["horse"], "avg_odds:", row["avg_odds"])
    print("=" * 80)

    lines = str(row["raw"]).splitlines()
    for i, line in enumerate(lines):
        print(f"{i:03}: {line}")