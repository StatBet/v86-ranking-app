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
    r2 = scores.get(2, 0)
    r3 = scores.get(3, 0)
    r4 = scores.get(4, 0)
    r5 = scores.get(5, 0)
    r8 = scores.get(8, 0)

    rows.append({
        "race_id": race_id,
        "winner_rank": int(winner.iloc[0]["model_rank"]),
        "gap_1_2": r1 - r2,
        "gap_1_3": r1 - r3,
        "gap_1_4": r1 - r4,
        "gap_1_5": r1 - r5,
        "spread_1_8": r1 - r8,
    })

races = pd.DataFrame(rows)

tests = [
    ("gap_1_2 >= 35", races["gap_1_2"] >= 35),
    ("gap_1_2 >= 40", races["gap_1_2"] >= 40),
    ("gap_1_3 >= 50", races["gap_1_3"] >= 50),
    ("gap_1_3 >= 60", races["gap_1_3"] >= 60),
    ("gap_1_3 >= 70", races["gap_1_3"] >= 70),
    ("gap_1_4 >= 60", races["gap_1_4"] >= 60),
    ("gap_1_4 >= 70", races["gap_1_4"] >= 70),
    ("gap_1_4 >= 80", races["gap_1_4"] >= 80),
    ("gap_1_5 >= 70", races["gap_1_5"] >= 70),
    ("gap_1_5 >= 80", races["gap_1_5"] >= 80),
    ("gap_1_5 >= 90", races["gap_1_5"] >= 90),
    ("spread_1_8 >= 80", races["spread_1_8"] >= 80),
    ("spread_1_8 >= 90", races["spread_1_8"] >= 90),
    ("spread_1_8 >= 100", races["spread_1_8"] >= 100),
]

print("=" * 80)
print("KANDIDATER FÖR 3-HÄSTARSLOPP")
print("=" * 80)

for name, mask in tests:
    subset = races[mask]

    if len(subset) == 0:
        continue

    top3 = (subset["winner_rank"] <= 3).mean() * 100
    top4 = (subset["winner_rank"] <= 4).mean() * 100
    top5 = (subset["winner_rank"] <= 5).mean() * 100

    print()
    print(name)
    print("-" * 40)
    print("Lopp:", len(subset))
    print("Rank 1-3:", round(top3, 1), "%")
    print("Rank 1-4:", round(top4, 1), "%")
    print("Rank 1-5:", round(top5, 1), "%")