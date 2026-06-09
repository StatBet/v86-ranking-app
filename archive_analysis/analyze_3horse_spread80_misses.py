import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values("model_rank")
    winner = race[race["won"] == 1]

    if winner.empty:
        continue

    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    spread_1_8 = scores.get(1, 0) - scores.get(8, 0)

    if spread_1_8 >= 80:
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
print("3-HÄSTARSLOPP: SPREAD 1-8 >= 80")
print("=" * 80)

print("Lopp:", len(clear))

for n in [1, 2, 3, 4, 5, 6, 8]:
    hits = (clear["winner_rank"] <= n).sum()
    print(f"Rank 1-{n}: {hits}/{len(clear)} = {round(hits / len(clear) * 100, 1)}%")

print()
print("=" * 80)
print("MISSAR TOPP 3")
print("=" * 80)

print(
    clear[clear["winner_rank"] > 3]
    .sort_values(["winner_rank", "date", "race_no"])
    .to_string(index=False)
)