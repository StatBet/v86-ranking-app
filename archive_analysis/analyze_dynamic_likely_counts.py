import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

race_rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("model_rank")

    winner = race[race["won"] == 1]

    if winner.empty:
        continue

    win_rank = int(winner.iloc[0]["model_rank"])

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

    race_rows.append({
        "race_id": race_id,
        "date": winner.iloc[0]["date"],
        "race_no": winner.iloc[0]["race_no"],
        "winner_rank": win_rank,
        "gap_1_2": r1 - r2,
        "gap_1_3": r1 - r3,
        "gap_1_4": r1 - r4,
        "gap_1_5": r1 - r5,
        "spread_1_8": r1 - r8,
    })

races = pd.DataFrame(race_rows)

tests = [
    ("LIKELY 1", races["winner_rank"] <= 1),
    ("LIKELY 2", races["winner_rank"] <= 2),
    ("LIKELY 3", races["winner_rank"] <= 3),
    ("LIKELY 4", races["winner_rank"] <= 4),
    ("LIKELY 5", races["winner_rank"] <= 5),
]

print("=" * 80)
print("BAS: FAST ANTAL TROLIGA")
print("=" * 80)

for name, mask in tests:
    print()
    print(name)
    print("-" * 40)
    print("Träffar:", int(mask.sum()))
    print("Lopp:", len(races))
    print("Träff%:", round(mask.mean() * 100, 1))

print()
print("=" * 80)
print("GAP-ANALYS")
print("=" * 80)

gap_tests = [
    ("gap_1_2 >= 10", races["gap_1_2"] >= 10),
    ("gap_1_2 >= 15", races["gap_1_2"] >= 15),
    ("gap_1_2 >= 30", races["gap_1_2"] >= 30),
    ("gap_1_2 >= 35", races["gap_1_2"] >= 35),
    ("gap_1_3 >= 40", races["gap_1_3"] >= 40),
    ("gap_1_3 >= 50", races["gap_1_3"] >= 50),
    ("gap_1_4 >= 50", races["gap_1_4"] >= 50),
    ("gap_1_4 >= 60", races["gap_1_4"] >= 60),
    ("spread_1_8 <= 40", races["spread_1_8"] <= 40),
    ("spread_1_8 <= 50", races["spread_1_8"] <= 50),
    ("spread_1_8 >= 70", races["spread_1_8"] >= 70),
]

for name, mask in gap_tests:
    subset = races[mask]

    print()
    print(name)
    print("-" * 40)
    print("Lopp:", len(subset))

    if len(subset):
        for n in [1, 2, 3, 4, 5]:
            hit = (subset["winner_rank"] <= n).mean() * 100
            print(f"Rank 1-{n}: {round(hit, 1)}%")