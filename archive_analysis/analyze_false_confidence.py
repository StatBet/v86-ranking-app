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

    spike = race.iloc[0]

    if spike["won"] == 1:
        continue

    winner = race[race["won"] == 1].iloc[0]

    second = race.iloc[1]

    score_gap = (
        spike["total_score"]
        - second["total_score"]
    )

    rows.append({
        "date": spike["date"],
        "race_no": spike["race_no"],
        "track": spike["track"],

        "spike_horse": spike["horse"],
        "winner_horse": winner["horse"],

        "total_score": spike["total_score"],
        "score_gap": score_gap,

        "post": spike["post"],
        "field_size": spike["field_size"],

        "win_percent": spike["win_percent"],
        "place_percent": spike["place_percent"],
        "form_score": spike["form_score"],
        "latest_start_score": spike["latest_start_score"],
        "driver_score": spike["driver_score"]
    })

a = pd.DataFrame(rows)

print("=" * 100)
print("50 HÖGST RANKADE FELSPIKAR")
print("=" * 100)

cols = [
    "date",
    "race_no",
    "spike_horse",
    "winner_horse",
    "total_score",
    "score_gap",
    "post",
    "field_size",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score"
]

print(
    a.sort_values(
        "total_score",
        ascending=False
    )
    .head(50)[cols]
    .to_string(index=False)
)