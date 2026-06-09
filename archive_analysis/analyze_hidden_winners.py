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

    spike = race.iloc[0]
    winner = race[race["won"] == 1].iloc[0]

    if spike["won"] == 1:
        continue

    rows.append({
        "winner_rank": int(
            race.index[race["won"] == 1][0] + 1
        ),

        "spike_post": spike["post"],
        "winner_post": winner["post"],

        "spike_latest": spike["latest_start_score"],
        "winner_latest": winner["latest_start_score"],

        "spike_form": spike["form_score"],
        "winner_form": winner["form_score"],

        "spike_win": spike["win_percent"],
        "winner_win": winner["win_percent"],

        "spike_place": spike["place_percent"],
        "winner_place": winner["place_percent"],

        "spike_driver": spike["driver_score"],
        "winner_driver": winner["driver_score"],

        "spike_gap": spike["total_score"] - race.iloc[1]["total_score"]
    })

a = pd.DataFrame(rows)

print("=" * 80)
print("VAR FANNS VINNAREN?")
print("=" * 80)

print(
    a["winner_rank"]
    .value_counts()
    .sort_index()
)

print()
print("=" * 80)
print("VINNARENS RANK I SNITT")
print("=" * 80)

print(
    round(a["winner_rank"].mean(), 2)
)

print()
print("=" * 80)
print("NÄR VINNAREN LÅG UTANFÖR TOPP 3")
print("=" * 80)

outside = a[a["winner_rank"] > 3]

print("Antal:", len(outside))

if len(outside):

    print()

    print(
        outside[[
            "winner_rank",
            "spike_post",
            "winner_post",
            "spike_latest",
            "winner_latest",
            "spike_form",
            "winner_form",
            "spike_win",
            "winner_win",
            "spike_place",
            "winner_place"
        ]]
        .mean()
        .round(2)
    )

print()
print("=" * 80)
print("NÄR VINNAREN VAR 2:A ELLER 3:A I MODELLEN")
print("=" * 80)

top3 = a[a["winner_rank"] <= 3]

print("Antal:", len(top3))

if len(top3):

    print()

    print(
        top3[[
            "winner_rank",
            "spike_post",
            "winner_post",
            "spike_latest",
            "winner_latest",
            "spike_form",
            "winner_form",
            "spike_win",
            "winner_win",
            "spike_place",
            "winner_place"
        ]]
        .mean()
        .round(2)
    )