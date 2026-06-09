import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("model_rank")
    winner = race[race["won"] == 1]

    if winner.empty:
        continue

    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}

    r1 = scores.get(1, 0)
    r3 = scores.get(3, 0)
    r4 = scores.get(4, 0)
    r8 = scores.get(8, 0)

    gap_1_3 = r1 - r3
    gap_1_4 = r1 - r4
    spread_1_8 = r1 - r8

    is_5horse = (
        (gap_1_3 >= 30)
        or (gap_1_3 >= 40)
        or (gap_1_4 >= 30)
        or (gap_1_4 >= 40)
        or (gap_1_4 >= 50)
    )

    rows.append({
        "race_id": race_id,
        "date": winner.iloc[0]["date"],
        "race_no": winner.iloc[0]["race_no"],
        "winner": winner.iloc[0]["horse"],
        "winner_rank": int(winner.iloc[0]["model_rank"]),
        "gap_1_3": gap_1_3,
        "gap_1_4": gap_1_4,
        "spread_1_8": spread_1_8,
        "is_5horse": is_5horse,
    })

races = pd.DataFrame(rows)
five = races[races["is_5horse"]]

print("=" * 80)
print("5-HÄSTARSLOPP - UNION")
print("=" * 80)

print("Lopp:", len(five))

for n in [3, 4, 5, 6, 8]:
    hits = (five["winner_rank"] <= n).sum()
    print(f"Rank 1-{n}: {hits}/{len(five)} = {round(hits / len(five) * 100, 1)}%")

print()
print("=" * 80)
print("MISSAR TOPP 5")
print("=" * 80)

print(
    five[five["winner_rank"] > 5]
    .sort_values(["winner_rank", "date", "race_no"])
    .to_string(index=False)
)