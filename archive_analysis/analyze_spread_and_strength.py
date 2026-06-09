import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 8:
        continue

    winner_rows = ranked[ranked["won"] == 1]

    if len(winner_rows) == 0:
        continue

    winner = winner_rows.iloc[0]

    top8 = ranked.head(8)

    rank1 = top8[top8["model_rank"] == 1].iloc[0]
    rank8 = top8[top8["model_rank"] == 8].iloc[0]

    spread = rank1["total_score"] - rank8["total_score"]
    avg_strength = top8["total_score"].mean()

    rows.append({
        "winner_rank": winner["model_rank"],
        "spread": spread,
        "avg_strength": avg_strength,
        "rank68_winner": int(
            winner["model_rank"] >= 6
            and winner["model_rank"] <= 8
        )
    })

res = pd.DataFrame(rows)

spread_limit = res["spread"].median()
strength_limit = res["avg_strength"].median()

res["spread_group"] = res["spread"].apply(
    lambda x: "Låg spread" if x <= spread_limit else "Hög spread"
)

res["strength_group"] = res["avg_strength"].apply(
    lambda x: "Hög styrka" if x >= strength_limit else "Låg styrka"
)

print("=" * 80)
print("SPREAD + STYRKA")
print("=" * 80)

print()
print("Spread-gräns:", round(spread_limit, 2))
print("Styrka-gräns:", round(strength_limit, 2))

summary = (
    res.groupby(["spread_group", "strength_group"])
    .agg(
        lopp=("rank68_winner", "count"),
        rank68_vinnare=("rank68_winner", "sum")
    )
    .reset_index()
)

summary["rank68_%"] = (
    summary["rank68_vinnare"]
    / summary["lopp"]
    * 100
).round(1)

print()
print(summary.to_string(index=False))

print()
print("=" * 80)
print("SNITT PER GRUPP")
print("=" * 80)

print(
    res.groupby(["spread_group", "strength_group"])[
        ["spread", "avg_strength", "rank68_winner"]
    ]
    .mean()
    .round(2)
    .to_string()
)