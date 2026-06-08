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

df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

rows = []

for race_id, race in df.groupby("race_id"):

    spike_top5 = set(
        race.nlargest(
            5,
            "spike_score"
        )["horse"]
    )

    winner = race[
        race["won"] == 1
    ].iloc[0]

    rank = int(winner["model_rank"])

    if (
        rank >= 6
        and rank <= 8
        and winner["horse"] in spike_top5
    ):
        rows.append({
            "date": winner["date"],
            "race_no": winner["race_no"],
            "horse": winner["horse"],
            "model_rank": rank,
            "avg_odds": winner["avg_odds"],
            "win_percent": winner["win_percent"],
            "place_percent": winner["place_percent"],
            "form_score": winner["form_score"],
            "latest_start_score": winner["latest_start_score"],
            "post": winner["post"]
        })

r = pd.DataFrame(rows)

print("=" * 80)
print("RANK 6-8 + SPIKE TOP5")
print("=" * 80)

print()
print("Antal:")
print(len(r))

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

print(
    r[
        [
            "model_rank",
            "avg_odds",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "post"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("ODDSBUCKETS")
print("=" * 80)

r["odds_bucket"] = pd.cut(
    r["avg_odds"],
    bins=[0,3,5,10,20,999],
    labels=[
        "<3",
        "3-5",
        "5-10",
        "10-20",
        "20+"
    ]
)

print(
    r["odds_bucket"]
    .value_counts()
    .sort_index()
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