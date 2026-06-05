import pandas as pd

df = pd.read_csv("ml_dataset.csv")
df = df[df["won"].isin([0, 1])]

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

    spike = race.iloc[0]
    winner = race[race["won"] == 1].iloc[0]

    if int(spike["won"]) == 1:
        continue

    rows.append({
        "race_id": race_id,
        "date": spike["date"],
        "race_no": spike["race_no"],
        "spike_horse": spike["horse"],
        "winner_horse": winner["horse"],

        "winner_better_post": int(winner["post"] < spike["post"]),
        "winner_better_latest": int(winner["latest_start_score"] > spike["latest_start_score"]),
        "winner_better_form": int(winner["form_score"] > spike["form_score"]),
        "winner_better_win_percent": int(winner["win_percent"] > spike["win_percent"]),
        "winner_better_place_percent": int(winner["place_percent"] > spike["place_percent"]),
        "winner_better_driver": int(winner["driver_score"] > spike["driver_score"]),
        "winner_better_avg_time": int(winner["avg_time"] < spike["avg_time"]),

        "post_diff": spike["post"] - winner["post"],
        "latest_diff": winner["latest_start_score"] - spike["latest_start_score"],
        "form_diff": winner["form_score"] - spike["form_score"],
        "win_percent_diff": winner["win_percent"] - spike["win_percent"],
        "place_percent_diff": winner["place_percent"] - spike["place_percent"],
        "driver_diff": winner["driver_score"] - spike["driver_score"],
        "avg_time_diff": spike["avg_time"] - winner["avg_time"],
        "total_score_diff": spike["total_score"] - winner["total_score"],
    })

a = pd.DataFrame(rows)

print("=" * 90)
print("VINNARE VS FELAKTIG SPIK")
print("=" * 90)
print("Felspikar:", len(a))

print()
print("=" * 90)
print("HUR OFTA HADE VINNAREN BÄTTRE VÄRDE?")
print("=" * 90)

cols = [
    "winner_better_post",
    "winner_better_latest",
    "winner_better_form",
    "winner_better_win_percent",
    "winner_better_place_percent",
    "winner_better_driver",
    "winner_better_avg_time",
]

for col in cols:
    print(
        f"{col:<35}",
        f"{round(a[col].mean() * 100, 1):>5}%"
    )

print()
print("=" * 90)
print("GENOMSNITTLIG SKILLNAD VINNARE - SPIK")
print("=" * 90)

diff_cols = [
    "post_diff",
    "latest_diff",
    "form_diff",
    "win_percent_diff",
    "place_percent_diff",
    "driver_diff",
    "avg_time_diff",
    "total_score_diff",
]

print(a[diff_cols].mean(numeric_only=True).round(2))

print()
print("=" * 90)
print("STÖRSTA MISSARNA - VINNAREN HADE MYCKET BÄTTRE LATEST START")
print("=" * 90)

print(
    a.sort_values(
        "latest_diff",
        ascending=False
    )
    .head(25)[[
        "date",
        "race_no",
        "spike_horse",
        "winner_horse",
        "latest_diff",
        "post_diff",
        "form_diff",
        "total_score_diff"
    ]]
    .to_string(index=False)
)

print()
print("=" * 90)
print("STÖRSTA MISSARNA - VINNAREN HADE BÄTTRE SPÅR")
print("=" * 90)

print(
    a.sort_values(
        "post_diff",
        ascending=False
    )
    .head(25)[[
        "date",
        "race_no",
        "spike_horse",
        "winner_horse",
        "post_diff",
        "latest_diff",
        "form_diff",
        "total_score_diff"
    ]]
    .to_string(index=False)
)