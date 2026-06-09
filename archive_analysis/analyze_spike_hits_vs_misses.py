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

hits = []
misses = []

for race_id, race in df.groupby("race_id"):

    winner = race[race["won"] == 1].iloc[0]

    rank = int(winner["model_rank"])

    if rank < 6 or rank > 8:
        continue

    spike_top5 = set(
        race.nlargest(
            5,
            "spike_score"
        )["horse"]
    )

    row = {
        "win_percent": winner["win_percent"],
        "place_percent": winner["place_percent"],
        "form_score": winner["form_score"],
        "latest_start_score": winner["latest_start_score"],
        "avg_odds": winner["avg_odds"],
        "post": winner["post"]
    }

    if winner["horse"] in spike_top5:
        hits.append(row)
    else:
        misses.append(row)

hits = pd.DataFrame(hits)
misses = pd.DataFrame(misses)

print("=" * 80)
print("SPIKE TRÄFFAR")
print("=" * 80)
print(hits.mean().round(2).to_string())

print()
print("=" * 80)
print("SPIKE MISSAR")
print("=" * 80)
print(misses.mean().round(2).to_string())