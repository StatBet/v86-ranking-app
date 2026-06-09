import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):
    fav = race[race["model_rank"] == 1]
    rank2 = race[race["model_rank"] == 2]

    if fav.empty or rank2.empty:
        continue

    fav = fav.iloc[0]
    rank2 = rank2.iloc[0]

    gap = fav["total_score"] - rank2["total_score"]

    is_tillagg = fav["post"] >= 6

    rows.append({
        "race_id": race_id,
        "date": fav["date"],
        "race_no": fav["race_no"],
        "horse": fav["horse"],
        "won": fav["won"],
        "post": fav["post"],
        "total_score": fav["total_score"],
        "gap_to_second": gap,
        "is_tillagg": is_tillagg
    })

res = pd.DataFrame(rows)

tillagg = res[res["is_tillagg"] == True]

print("=" * 80)
print("FAVORITER FRÅN TILLÄGG - GAPFILTER")
print("=" * 80)

for gap in [0, 10, 15, 20, 25, 30]:
    subset = tillagg[tillagg["gap_to_second"] >= gap]

    print()
    print(f"Gap >= {gap}")
    print("-" * 40)
    print("Antal:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print("Träff%:", round(subset["won"].mean() * 100, 1) if len(subset) else 0)