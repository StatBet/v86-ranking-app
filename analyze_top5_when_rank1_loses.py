import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rows = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if race["won"].sum() != 1:
        continue

    winner_rank = int(
        race.index[race["won"] == 1][0] + 1
    )

    rank1 = race.iloc[0]
    rank2 = race.iloc[1] if len(race) >= 2 else None

    if rank1["won"] == 1:
        continue

    score_gap = (
        rank1["total_score"]
        - race.iloc[1]["total_score"]
    )

    rows.append({
        "winner_rank": winner_rank,

        "rank1_post": rank1["post"],
        "rank2_post": rank2["post"],

        "field_size": rank1["field_size"],

        "score_gap": score_gap,

        "rank1_bad_post": int(
            rank1["post"] >= 7
        ),

        "rank2_good_post": int(
            rank2["post"] <= 6
        ),

        "gap_lt_10": int(
            score_gap < 10
        ),

        "gap_lt_20": int(
            score_gap < 20
        )
    })

a = pd.DataFrame(rows)

print("=" * 80)
print("NÄR RANK 1 FÖRLORAR")
print("=" * 80)

print(
    a["winner_rank"]
    .value_counts()
    .sort_index()
)

print()
print("=" * 80)
print("TOPP 5")
print("=" * 80)

for rank in [2, 3, 4, 5]:

    count = (a["winner_rank"] == rank).sum()

    pct = round(
        count / len(a) * 100,
        1
    )

    print(
        f"Rank {rank}: {count} ({pct}%)"
    )

print()
print("=" * 80)
print("MILJÖFALL")
print("=" * 80)

cases = a[
    (a["rank1_post"] >= 7)
    &
    (a["rank2_post"] <= 6)
    &
    (a["score_gap"] < 10)
]

print("Lopp:", len(cases))
print()

for rank in [2, 3, 4, 5]:

    count = (
        cases["winner_rank"] == rank
    ).sum()

    pct = round(
        count / len(cases) * 100,
        1
    ) if len(cases) else 0

    print(
        f"Rank {rank}: {count} ({pct}%)"
    )

print()
print("=" * 80)
print("MILJÖFALL + GAP < 20")
print("=" * 80)

cases = a[
    (a["rank1_post"] >= 7)
    &
    (a["rank2_post"] <= 6)
    &
    (a["score_gap"] < 20)
]

print("Lopp:", len(cases))
print()

for rank in [2, 3, 4, 5]:

    count = (
        cases["winner_rank"] == rank
    ).sum()

    pct = round(
        count / len(cases) * 100,
        1
    ) if len(cases) else 0

    print(
        f"Rank {rank}: {count} ({pct}%)"
    )