import pandas as pd

df = pd.read_csv("ml_dataset.csv")

zero = df[df["avg_odds"] == 0].copy()

print("=" * 80)
print("RAW EXEMPEL - AVG_ODDS = 0")
print("=" * 80)

for _, row in zero.head(10).iterrows():
    print()
    print("=" * 80)
    print(row["date"], "Avd", row["race_no"], row["horse"])
    print("Starter:", row["starts"])
    print("Avg odds:", row["avg_odds"])
    print("=" * 80)
    print(row["raw"][:3000])