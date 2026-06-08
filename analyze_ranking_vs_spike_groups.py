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

# Enkel spike-score
df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

both = 0
ranking_only = 0
spike_only = 0
neither = 0

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

    if ranking_hit and spike_hit:
        both += 1

    elif ranking_hit and not spike_hit:
        ranking_only += 1

    elif not ranking_hit and spike_hit:
        spike_only += 1

    else:
        neither += 1

print("=" * 80)
print("RANKING VS SPIKE")
print("=" * 80)

print()
print("Both")
print(both)

print()
print("Ranking only")
print(ranking_only)

print()
print("Spike only")
print(spike_only)

print()
print("Neither")
print(neither)