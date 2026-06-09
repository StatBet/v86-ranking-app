import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

spreads = {}

for race_id, race in df.groupby("race_id"):
    r1 = race[race["model_rank"] == 1]
    r8 = race[race["model_rank"] == 8]

    if r1.empty or r8.empty:
        continue

    spreads[race_id] = (
        r1.iloc[0]["total_score"]
        - r8.iloc[0]["total_score"]
    )

df["spread"] = df["race_id"].map(spreads).fillna(0)

df.to_csv("ml_dataset.csv", index=False)

print("=" * 80)
print("ML DATASET FIXAT")
print("=" * 80)
print("Tillagda kolumner:")
print("- spike_score")
print("- spread")
print()
print("Rader:", len(df))
print("Lopp:", df["race_id"].nunique())
print("Vinnare:", int(df["won"].sum()))