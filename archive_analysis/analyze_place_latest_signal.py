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

df = df[
    df["race_id"].isin(valid_races)
].copy()

rows = []

for race_id, race in df.groupby("race_id"):

    winner = race[
        race["won"] == 1
    ].iloc[0]

    rank = int(winner["model_rank"])

    if rank < 6 or rank > 8:
        continue

    if (
        winner["place_percent"] >= 50
        and winner["latest_start_score"] >= 5
    ):
        rows.append({
            "date": winner["date"],
            "race_no": winner["race_no"],
            "horse": winner["horse"],
            "model_rank": rank,
            "place_percent": winner["place_percent"],
            "latest_start_score": winner["latest_start_score"],
            "win_percent": winner["win_percent"],
            "form_score": winner["form_score"],
            "avg_odds": winner["avg_odds"]
        })

r = pd.DataFrame(rows)

print("=" * 80)
print("RANK 6-8 + PLACE% + LATEST")
print("=" * 80)

print()
print("Antal vinnare:")
print(len(r))

print()
print("=" * 80)
print("MODEL RANK")
print("=" * 80)

print(
    r["model_rank"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

print(
    r[
        [
            "model_rank",
            "place_percent",
            "latest_start_score",
            "win_percent",
            "form_score",
            "avg_odds"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("ALLA")
print("=" * 80)

print(
    r.sort_values(
        "avg_odds",
        ascending=False
    )
    .to_string(index=False)
)