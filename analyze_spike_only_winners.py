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

# Samma spike-score som förra analysen
df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

spike_only_rows = []

for race_id, race in df.groupby("race_id"):

    ranking_top5 = race.nsmallest(
        5,
        "model_rank"
    )

    spike_top5 = race.nlargest(
        5,
        "spike_score"
    )

    ranking_hit = ranking_top5["won"].sum() > 0
    spike_hit = spike_top5["won"].sum() > 0

    if (not ranking_hit) and spike_hit:

        winner = race[
            race["won"] == 1
        ].iloc[0]

        spike_only_rows.append({
            "date": winner["date"],
            "race_no": winner["race_no"],
            "horse": winner["horse"],
            "model_rank": winner["model_rank"],
            "percent": winner["percent"],
            "win_percent": winner["win_percent"],
            "place_percent": winner["place_percent"],
            "form_score": winner["form_score"],
            "latest_start_score": winner["latest_start_score"],
            "post": winner["post"],
            "avg_odds": winner["avg_odds"]
        })

spike_df = pd.DataFrame(spike_only_rows)

print("=" * 80)
print("SPIKE ONLY VINNARE")
print("=" * 80)

print()
print("Antal:")
print(len(spike_df))

print()
print("=" * 80)
print("MODEL RANK")
print("=" * 80)

print(
    spike_df["model_rank"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

cols = [
    "model_rank",
    "percent",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "post",
    "avg_odds"
]

print(
    spike_df[cols]
    .mean()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("TOPP 30 SPIKE ONLY")
print("=" * 80)

print(
    spike_df.sort_values(
        "model_rank"
    )
    .head(30)
    .to_string(index=False)
)