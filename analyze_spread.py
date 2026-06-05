import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rows = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 5:
        continue

    if race["won"].sum() != 1:
        continue

    winner_rank = int(
        race.index[race["won"] == 1][0] + 1
    )

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]
    rank3 = race.iloc[2]
    rank5 = race.iloc[4]

    top2_spread = (
        rank1["total_score"]
        - rank2["total_score"]
    )

    top3_spread = (
        rank1["total_score"]
        - rank3["total_score"]
    )

    top5_spread = (
        rank1["total_score"]
        - rank5["total_score"]
    )

    rows.append({
        "winner_rank": winner_rank,
        "rank1_won": int(winner_rank == 1),
        "top2_spread": top2_spread,
        "top3_spread": top3_spread,
        "top5_spread": top5_spread
    })

a = pd.DataFrame(rows)

print("=" * 80)
print("SPREADANALYS")
print("=" * 80)

print()
print("NÄR RANK1 VANN")
print("-" * 40)

print(
    a[a["rank1_won"] == 1][[
        "top2_spread",
        "top3_spread",
        "top5_spread"
    ]].mean()
)

print()
print("NÄR RANK1 FÖRLORADE")
print("-" * 40)

print(
    a[a["rank1_won"] == 0][[
        "top2_spread",
        "top3_spread",
        "top5_spread"
    ]].mean()
)

print()
print("=" * 80)
print("TOP5 SPREAD BUCKETS")
print("=" * 80)

bins = [0, 10, 20, 30, 40, 999]
labels = [
    "0-10",
    "10-20",
    "20-30",
    "30-40",
    "40+"
]

a["spread_bucket"] = pd.cut(
    a["top5_spread"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

summary = (
    a.groupby("spread_bucket")
    .agg(
        lopp=("rank1_won", "size"),
        ratt=("rank1_won", "sum")
    )
    .reset_index()
)

summary["traff_pct"] = (
    summary["ratt"]
    / summary["lopp"]
    * 100
).round(1)

print(summary.to_string(index=False))

print()
print("=" * 80)
print("TOP3 SPREAD BUCKETS")
print("=" * 80)

a["spread_bucket"] = pd.cut(
    a["top3_spread"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

summary = (
    a.groupby("spread_bucket")
    .agg(
        lopp=("rank1_won", "size"),
        ratt=("rank1_won", "sum")
    )
    .reset_index()
)

summary["traff_pct"] = (
    summary["ratt"]
    / summary["lopp"]
    * 100
).round(1)

print(summary.to_string(index=False))