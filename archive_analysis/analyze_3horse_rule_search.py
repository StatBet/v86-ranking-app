import pandas as pd
from itertools import combinations

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("model_rank")
    winner = race[race["won"] == 1]

    if winner.empty:
        continue

    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)

    rows.append({
        "race_id": race_id,
        "winner_rank": int(winner.iloc[0]["model_rank"]),
        "gap_1_2": r1 - scores.get(2, 0),
        "gap_1_3": r1 - scores.get(3, 0),
        "gap_1_4": r1 - scores.get(4, 0),
        "gap_1_5": r1 - scores.get(5, 0),
        "spread_1_8": r1 - scores.get(8, 0),
    })

races = pd.DataFrame(rows)

conditions = {
    "gap_1_2 >= 25": races["gap_1_2"] >= 25,
    "gap_1_2 >= 30": races["gap_1_2"] >= 30,
    "gap_1_2 >= 35": races["gap_1_2"] >= 35,
    "gap_1_3 >= 40": races["gap_1_3"] >= 40,
    "gap_1_3 >= 45": races["gap_1_3"] >= 45,
    "gap_1_3 >= 50": races["gap_1_3"] >= 50,
    "gap_1_4 >= 50": races["gap_1_4"] >= 50,
    "gap_1_4 >= 55": races["gap_1_4"] >= 55,
    "gap_1_4 >= 60": races["gap_1_4"] >= 60,
    "gap_1_5 >= 60": races["gap_1_5"] >= 60,
    "gap_1_5 >= 70": races["gap_1_5"] >= 70,
    "spread_1_8 >= 75": races["spread_1_8"] >= 75,
    "spread_1_8 >= 80": races["spread_1_8"] >= 80,
    "spread_1_8 >= 85": races["spread_1_8"] >= 85,
    "spread_1_8 >= 90": races["spread_1_8"] >= 90,
}

results = []

# Enskilda regler
for name, mask in conditions.items():
    subset = races[mask]
    if len(subset) == 0:
        continue

    results.append({
        "rule": name,
        "races": len(subset),
        "top3_hits": int((subset["winner_rank"] <= 3).sum()),
        "top3_pct": round((subset["winner_rank"] <= 3).mean() * 100, 1),
        "top4_pct": round((subset["winner_rank"] <= 4).mean() * 100, 1),
        "top5_pct": round((subset["winner_rank"] <= 5).mean() * 100, 1),
    })

# Kombinationer: A AND B
for (name1, mask1), (name2, mask2) in combinations(conditions.items(), 2):
    mask = mask1 & mask2
    subset = races[mask]

    if len(subset) < 20:
        continue

    results.append({
        "rule": f"{name1} AND {name2}",
        "races": len(subset),
        "top3_hits": int((subset["winner_rank"] <= 3).sum()),
        "top3_pct": round((subset["winner_rank"] <= 3).mean() * 100, 1),
        "top4_pct": round((subset["winner_rank"] <= 4).mean() * 100, 1),
        "top5_pct": round((subset["winner_rank"] <= 5).mean() * 100, 1),
    })

res = pd.DataFrame(results)

print("=" * 80)
print("3-HÄSTARSREGLER - ALLA")
print("=" * 80)

print(
    res.sort_values(["top3_pct", "races"], ascending=[False, False])
    .head(60)
    .to_string(index=False)
)

print()
print("=" * 80)
print("KANDIDATER: CA 80-120 LOPP")
print("=" * 80)

candidate = res[
    (res["races"] >= 80)
    & (res["races"] <= 120)
].copy()

print(
    candidate.sort_values(["top3_pct", "races"], ascending=[False, False])
    .to_string(index=False)
)

print()
print("=" * 80)
print("KANDIDATER: MINST 60 LOPP OCH TOP3 >= 78%")
print("=" * 80)

candidate2 = res[
    (res["races"] >= 60)
    & (res["top3_pct"] >= 78)
].copy()

print(
    candidate2.sort_values(["top3_pct", "races"], ascending=[False, False])
    .to_string(index=False)
)