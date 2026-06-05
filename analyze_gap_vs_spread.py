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

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]
    rank3 = race.iloc[2]
    rank5 = race.iloc[4]

    rows.append({
        "rank1_won": int(rank1["won"]),

        "score_gap": (
            rank1["total_score"]
            - rank2["total_score"]
        ),

        "top3_spread": (
            rank1["total_score"]
            - rank3["total_score"]
        ),

        "top5_spread": (
            rank1["total_score"]
            - rank5["total_score"]
        )
    })

a = pd.DataFrame(rows)

print("=" * 80)
print("KORRELATIONER")
print("=" * 80)

print()
print("score_gap vs top3_spread")
print(
    round(
        a["score_gap"].corr(
            a["top3_spread"]
        ),
        3
    )
)

print()
print("score_gap vs top5_spread")
print(
    round(
        a["score_gap"].corr(
            a["top5_spread"]
        ),
        3
    )
)

print()
print("=" * 80)
print("SNITT PER SCORE GAP")
print("=" * 80)

bins = [0, 5, 10, 15, 20, 30, 999]
labels = [
    "0-5",
    "5-10",
    "10-15",
    "15-20",
    "20-30",
    "30+"
]

a["gap_bucket"] = pd.cut(
    a["score_gap"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

summary = (
    a.groupby("gap_bucket")
    .agg(
        lopp=("rank1_won", "size"),
        traff=("rank1_won", "mean"),
        top3=("top3_spread", "mean"),
        top5=("top5_spread", "mean")
    )
    .reset_index()
)

summary["traff"] = (
    summary["traff"] * 100
).round(1)

summary["top3"] = summary["top3"].round(1)
summary["top5"] = summary["top5"].round(1)

print(summary.to_string(index=False))

print()
print("=" * 80)
print("LÅGT GAP MEN STORT SPREAD")
print("=" * 80)

special = a[
    (a["score_gap"] < 10)
    &
    (a["top3_spread"] >= 30)
]

print("Lopp:", len(special))

if len(special):
    print(
        "Rank1 träff:",
        round(
            special["rank1_won"].mean() * 100,
            1
        ),
        "%"
    )

print()
print("=" * 80)
print("HÖGT GAP MEN LITET SPREAD")
print("=" * 80)

special = a[
    (a["score_gap"] >= 20)
    &
    (a["top3_spread"] < 20)
]

print("Lopp:", len(special))

if len(special):
    print(
        "Rank1 träff:",
        round(
            special["rank1_won"].mean() * 100,
            1
        ),
        "%"
    )