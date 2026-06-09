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

positions = []

details = []

for race_id, race in df.groupby("race_id"):

    winner = race[
        race["won"] == 1
    ].iloc[0]

    winner_rank = int(winner["model_rank"])

    if winner_rank < 6 or winner_rank > 8:
        continue

    spike_ranked = race.sort_values(
        "spike_score",
        ascending=False
    ).reset_index(drop=True)

    spike_ranked["spike_rank"] = (
        spike_ranked.index + 1
    )

    winner_row = spike_ranked[
        spike_ranked["horse"] == winner["horse"]
    ]

    if winner_row.empty:
        continue

    spike_rank = int(
        winner_row.iloc[0]["spike_rank"]
    )

    if spike_rank <= 5:

        positions.append(spike_rank)

        details.append({
            "date": winner["date"],
            "race_no": winner["race_no"],
            "horse": winner["horse"],
            "model_rank": winner_rank,
            "spike_rank": spike_rank,
            "spike_score": round(
                winner_row.iloc[0]["spike_score"],
                2
            ),
            "avg_odds": winner["avg_odds"]
        })

details_df = pd.DataFrame(details)

print("=" * 80)
print("RANK 6-8 VINNARE SOM SPIKE FÅNGAR")
print("=" * 80)

print()
print("Antal:")
print(len(details_df))

print()
print("=" * 80)
print("SPIKE RANK")
print("=" * 80)

print(
    pd.Series(positions)
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

print(
    details_df[
        [
            "model_rank",
            "spike_rank",
            "avg_odds"
        ]
    ]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("ALLA VINNARE")
print("=" * 80)

print(
    details_df
    .sort_values(
        ["spike_rank", "model_rank"]
    )
    .to_string(index=False)
)