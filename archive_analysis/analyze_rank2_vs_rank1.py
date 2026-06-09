import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rows = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        continue

    if race["won"].sum() != 1:
        continue

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]
    winner = race[race["won"] == 1].iloc[0]
    winner_rank = int(race.index[race["won"] == 1][0] + 1)

    rows.append({
        "winner_rank": winner_rank,
        "rank1_won": int(rank1["won"]),
        "rank2_won": int(rank2["won"]),

        "rank1_post": rank1["post"],
        "rank2_post": rank2["post"],
        "post_diff_rank1_minus_rank2": rank1["post"] - rank2["post"],

        "rank1_field_size": rank1["field_size"],
        "rank2_field_size": rank2["field_size"],

        "rank1_total": rank1["total_score"],
        "rank2_total": rank2["total_score"],
        "score_gap": rank1["total_score"] - rank2["total_score"],

        "rank1_latest": rank1["latest_start_score"],
        "rank2_latest": rank2["latest_start_score"],
        "latest_diff_rank2_minus_rank1": rank2["latest_start_score"] - rank1["latest_start_score"],

        "rank1_form": rank1["form_score"],
        "rank2_form": rank2["form_score"],
        "form_diff_rank2_minus_rank1": rank2["form_score"] - rank1["form_score"],

        "rank1_win": rank1["win_percent"],
        "rank2_win": rank2["win_percent"],
        "win_diff_rank2_minus_rank1": rank2["win_percent"] - rank1["win_percent"],

        "rank1_place": rank1["place_percent"],
        "rank2_place": rank2["place_percent"],
        "place_diff_rank2_minus_rank1": rank2["place_percent"] - rank1["place_percent"],

        "rank1_driver": rank1["driver_score"],
        "rank2_driver": rank2["driver_score"],
        "driver_diff_rank2_minus_rank1": rank2["driver_score"] - rank1["driver_score"],
    })

a = pd.DataFrame(rows)

rank1_wins = a[a["rank1_won"] == 1]
rank2_wins = a[a["rank2_won"] == 1]

print("=" * 90)
print("RANK 1 VS RANK 2")
print("=" * 90)

print("Alla lopp:", len(a))
print("Rank 1 vann:", len(rank1_wins))
print("Rank 2 vann:", len(rank2_wins))

print()
print("=" * 90)
print("NÄR RANK 2 VANN")
print("=" * 90)

print(
    rank2_wins[[
        "score_gap",
        "post_diff_rank1_minus_rank2",
        "latest_diff_rank2_minus_rank1",
        "form_diff_rank2_minus_rank1",
        "win_diff_rank2_minus_rank1",
        "place_diff_rank2_minus_rank1",
        "driver_diff_rank2_minus_rank1",
        "rank1_post",
        "rank2_post",
        "rank1_field_size"
    ]]
    .mean()
    .round(2)
)

print()
print("=" * 90)
print("NÄR RANK 1 VANN")
print("=" * 90)

print(
    rank1_wins[[
        "score_gap",
        "post_diff_rank1_minus_rank2",
        "latest_diff_rank2_minus_rank1",
        "form_diff_rank2_minus_rank1",
        "win_diff_rank2_minus_rank1",
        "place_diff_rank2_minus_rank1",
        "driver_diff_rank2_minus_rank1",
        "rank1_post",
        "rank2_post",
        "rank1_field_size"
    ]]
    .mean()
    .round(2)
)

print()
print("=" * 90)
print("RANK 2 VANN - MILJÖFILTER")
print("=" * 90)

checks = [
    (
        "rank1 post >= 7 och rank2 post <= 6",
        (a["rank1_post"] >= 7) &
        (a["rank2_post"] <= 6)
    ),
    (
        "rank1 post >= 9 och rank2 post <= 6",
        (a["rank1_post"] >= 9) &
        (a["rank2_post"] <= 6)
    ),
    (
        "rank1 post >= 7, rank2 post <= 6, gap < 20",
        (a["rank1_post"] >= 7) &
        (a["rank2_post"] <= 6) &
        (a["score_gap"] < 20)
    ),
    (
        "rank1 post >= 7, rank2 post <= 6, gap < 10",
        (a["rank1_post"] >= 7) &
        (a["rank2_post"] <= 6) &
        (a["score_gap"] < 10)
    ),
    (
        "rank2 latest bättre än rank1",
        a["latest_diff_rank2_minus_rank1"] > 0
    ),
    (
        "rank2 form bättre än rank1",
        a["form_diff_rank2_minus_rank1"] > 0
    ),
]

for name, condition in checks:
    subset = a[condition]

    total = len(subset)
    r1 = int(subset["rank1_won"].sum()) if total else 0
    r2 = int(subset["rank2_won"].sum()) if total else 0

    r1_pct = round(r1 / total * 100, 1) if total else 0
    r2_pct = round(r2 / total * 100, 1) if total else 0

    print()
    print(name)
    print("Lopp:", total)
    print("Rank1 vann:", r1, f"({r1_pct}%)")
    print("Rank2 vann:", r2, f"({r2_pct}%)")