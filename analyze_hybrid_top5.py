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

ranking_hits = 0
hybrid_hits = 0
total_races = 0

for race_id, race in df.groupby("race_id"):

    total_races += 1

    ranking_top5 = set(
        race[
            race["model_rank"] <= 5
        ]["horse"]
    )

    rank12 = race[
        race["model_rank"] <= 2
    ]

    spike_candidates = race[
        race["model_rank"].between(6, 8)
    ]

    spike_candidates = spike_candidates.sort_values(
        "spike_score",
        ascending=False
    ).head(3)

    hybrid = pd.concat([
        rank12,
        spike_candidates
    ])

    hybrid_top5 = set(
        hybrid["horse"]
    )

    winner = race[
        race["won"] == 1
    ].iloc[0]["horse"]

    if winner in ranking_top5:
        ranking_hits += 1

    if winner in hybrid_top5:
        hybrid_hits += 1

print("=" * 80)
print("TOP5 VS HYBRID")
print("=" * 80)

print()
print("Nuvarande Top5")
print("----------------")
print("Träffar:", ranking_hits)
print("Lopp:", total_races)
print(
    "Träff%:",
    round(ranking_hits / total_races * 100, 1)
)

print()
print("Hybrid A")
print("----------------")
print("Träffar:", hybrid_hits)
print("Lopp:", total_races)
print(
    "Träff%:",
    round(hybrid_hits / total_races * 100, 1)
)