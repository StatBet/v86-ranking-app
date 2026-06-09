import pandas as pd

df = pd.read_csv("ml_dataset.csv")

lost_rows = []
gained_rows = []

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

    score_gap = (
        rank1["total_score"]
        - rank2["total_score"]
    )

    override = (
        rank1["post"] >= 7
        and rank2["post"] <= 6
        and score_gap < 10
    )

    if not override:
        continue

    winner = race[race["won"] == 1].iloc[0]

    row = {
        "date": rank1["date"],
        "race_no": rank1["race_no"],

        "rank1": rank1["horse"],
        "rank2": rank2["horse"],
        "winner": winner["horse"],

        "gap": round(score_gap, 1),

        "rank1_post": rank1["post"],
        "rank2_post": rank2["post"],

        "rank1_form": rank1["form_score"],
        "rank2_form": rank2["form_score"],

        "rank1_latest": rank1["latest_start_score"],
        "rank2_latest": rank2["latest_start_score"],

        "rank1_win": rank1["win_percent"],
        "rank2_win": rank2["win_percent"]
    }

    if rank1["won"] == 1:
        lost_rows.append(row)

    if rank2["won"] == 1:
        gained_rows.append(row)

print("=" * 100)
print("FÖRLORADE VINNARE (RANK1 VAR RÄTT)")
print("=" * 100)

print("Antal:", len(lost_rows))
print()

if lost_rows:
    print(
        pd.DataFrame(lost_rows)
        .sort_values("gap")
        .to_string(index=False)
    )

print()
print("=" * 100)
print("NYA VINNARE (RANK2 VAR RÄTT)")
print("=" * 100)

print("Antal:", len(gained_rows))
print()

if gained_rows:
    print(
        pd.DataFrame(gained_rows)
        .sort_values("gap")
        .to_string(index=False)
    )