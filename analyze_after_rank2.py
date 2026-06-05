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

    if winner_rank <= 2:
        continue

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]
    winner = race[race["won"] == 1].iloc[0]

    rows.append({
        "winner_rank": winner_rank,

        "rank1_post": rank1["post"],
        "rank2_post": rank2["post"],
        "winner_post": winner["post"],

        "rank1_latest": rank1["latest_start_score"],
        "rank2_latest": rank2["latest_start_score"],
        "winner_latest": winner["latest_start_score"],

        "rank1_form": rank1["form_score"],
        "rank2_form": rank2["form_score"],
        "winner_form": winner["form_score"],

        "rank1_win": rank1["win_percent"],
        "rank2_win": rank2["win_percent"],
        "winner_win": winner["win_percent"],

        "score_gap": (
            rank1["total_score"]
            - rank2["total_score"]
        )
    })

a = pd.DataFrame(rows)

print("=" * 90)
print("NÄR VARKEN RANK1 ELLER RANK2 VANN")
print("=" * 90)

print("Antal lopp:", len(a))

print()
print("=" * 90)
print("VINNARENS RANK")
print("=" * 90)

print(
    a["winner_rank"]
    .value_counts()
    .sort_index()
)

print()
print("=" * 90)
print("SNITT")
print("=" * 90)

print(
    a[[
        "rank1_post",
        "rank2_post",
        "winner_post",
        "rank1_latest",
        "rank2_latest",
        "winner_latest",
        "rank1_form",
        "rank2_form",
        "winner_form",
        "rank1_win",
        "rank2_win",
        "winner_win",
        "score_gap"
    ]]
    .mean()
)

print()
print("=" * 90)
print("VINNAREN HADE BÄTTRE ÄN BÅDE RANK1 OCH RANK2")
print("=" * 90)

for feature in [
    "post",
    "latest",
    "form",
    "win"
]:

    if feature == "post":
        better = (
            (a["winner_post"] < a["rank1_post"])
            &
            (a["winner_post"] < a["rank2_post"])
        )

    else:
        better = (
            (a[f"winner_{feature}"] > a[f"rank1_{feature}"])
            &
            (a[f"winner_{feature}"] > a[f"rank2_{feature}"])
        )

    print(
        feature,
        round(better.mean() * 100, 1),
        "%"
    )