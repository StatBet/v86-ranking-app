import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[
    valid_races["won"] == 1
]["race_id"]

df = df[df["race_id"].isin(valid_races)].copy()

print("=" * 80)
print("RANKPOSITIONER TOPP 5")
print("=" * 80)

total_races = df["race_id"].nunique()

for rank in [1, 2, 3, 4, 5]:
    subset = df[df["model_rank"] == rank]

    wins = int(subset["won"].sum())
    pct = round(wins / total_races * 100, 1)

    print()
    print(f"Rank {rank}")
    print("-" * 40)
    print("Vinnare:", wins)
    print("Träff% av lopp:", pct)

print()
print("=" * 80)
print("TOPP 5 TOTALT")
print("=" * 80)

top5 = df[df["model_rank"] <= 5]

hits = (
    top5.groupby("race_id")["won"]
    .sum()
    .gt(0)
    .sum()
)

print("Träffar:", int(hits))
print("Lopp:", total_races)
print("Träff%:", round(hits / total_races * 100, 1))