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

df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

ranking_hits = 0
hybrid_hits = 0

for race_id, race in df.groupby("race_id"):

    ranking_top5 = set(
        race[
            race["model_rank"] <= 5
        ]["horse"]
    )

    winner = race[
        race["won"] == 1
    ].iloc[0]["horse"]

    if winner in ranking_top5:
        ranking_hits += 1

    rank1_4 = race[
        race["model_rank"] <= 4
    ].copy()

    candidates = race[
        ~race["horse"].isin(
            rank1_4["horse"]
        )
    ].copy()

    if len(candidates):

        spike_pick = (
            candidates
            .sort_values(
                "spike_score",
                ascending=False
            )
            .iloc[0]["horse"]
        )

        hybrid_top5 = set(
            rank1_4["horse"]
        )

        hybrid_top5.add(
            spike_pick
        )

    else:
        hybrid_top5 = set(
            rank1_4["horse"]
        )

    if winner in hybrid_top5:
        hybrid_hits += 1

print("=" * 80)
print("HYBRID B")
print("=" * 80)

print()
print("Nuvarande Top5")
print("----------------")
print("Träffar:", ranking_hits)
print("Träff%:", round(ranking_hits / 510 * 100, 1))

print()
print("Rank1-4 + Bästa Spike")
print("----------------")
print("Träffar:", hybrid_hits)
print("Träff%:", round(hybrid_hits / 510 * 100, 1))

print()
print("Skillnad:")
print(hybrid_hits - ranking_hits)