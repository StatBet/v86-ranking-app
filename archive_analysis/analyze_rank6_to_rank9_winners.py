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

results = []

for race_id, race in df.groupby("race_id"):

    winner = race[
        race["won"] == 1
    ].iloc[0]

    winner_rank = int(winner["model_rank"])

    if winner_rank < 6 or winner_rank > 9:
        continue

    spike_top5 = set(
        race.nlargest(
            5,
            "spike_score"
        )["horse"]
    )

    caught_by_spike = (
        winner["horse"] in spike_top5
    )

    results.append({
        "winner_rank": winner_rank,
        "caught_by_spike": int(caught_by_spike)
    })

r = pd.DataFrame(results)

print("=" * 80)
print("VINNARE RANK 6-9")
print("=" * 80)

for rank in [6, 7, 8, 9]:

    subset = r[
        r["winner_rank"] == rank
    ]

    total = len(subset)

    caught = int(
        subset["caught_by_spike"].sum()
    )

    pct = round(
        caught / total * 100,
        1
    ) if total else 0

    print()
    print(f"Rank {rank}")
    print(f"Vinnare: {total}")
    print(f"Spike fångar: {caught}")
    print(f"Träff%: {pct}")