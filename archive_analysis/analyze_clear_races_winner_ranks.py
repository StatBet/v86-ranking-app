import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("model_rank")

    winner = race[race["won"] == 1]
    if winner.empty:
        continue

    scores = {
        int(row["model_rank"]): row["total_score"]
        for _, row in race.iterrows()
    }

    r1 = scores.get(1, 0)
    r8 = scores.get(8, 0)

    spread_1_8 = r1 - r8

    if spread_1_8 >= 70:
        rows.append({
            "race_id": race_id,
            "date": winner.iloc[0]["date"],
            "race_no": winner.iloc[0]["race_no"],
            "winner": winner.iloc[0]["horse"],
            "winner_rank": int(winner.iloc[0]["model_rank"]),
            "spread_1_8": spread_1_8,
        })

clear = pd.DataFrame(rows)

print("=" * 80)
print("TYDLIGA LOPP: SPREAD 1-8 >= 70")
print("=" * 80)

print()
print("Antal lopp:", len(clear))

for n in [1, 2, 3, 4, 5, 6, 8]:
    hits = (clear["winner_rank"] <= n).sum()
    print(
        f"Rank 1-{n}:",
        hits,
        "/",
        len(clear),
        "=",
        round(hits / len(clear) * 100, 1),
        "%"
    )

print()
print("=" * 80)
print("VINNARRANK-FÖRDELNING")
print("=" * 80)

print(
    clear["winner_rank"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("=" * 80)
print("VINNARE UTANFÖR RANK 3")
print("=" * 80)

print(
    clear[clear["winner_rank"] > 3]
    .sort_values(["winner_rank", "date", "race_no"])
    .to_string(index=False)
)