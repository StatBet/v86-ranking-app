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

    top = race.iloc[0]
    second = race.iloc[1]

    score_gap = (
        top["total_score"]
        - second["total_score"]
    )

    rows.append({
        "won": int(top["won"]),

        "post_1_6": int(top["post"] <= 6),
        "post_7_8": int(
            7 <= top["post"] <= 8
        ),
        "post_9_plus": int(
            top["post"] >= 9
        ),

        "field_le_10": int(
            top["field_size"] <= 10
        ),
        "field_11_12": int(
            11 <= top["field_size"] <= 12
        ),
        "field_13_plus": int(
            top["field_size"] >= 13
        ),

        "gap_10": int(score_gap >= 10),
        "gap_20": int(score_gap >= 20),
        "gap_30": int(score_gap >= 30),

        "latest_10": int(
            top["latest_start_score"] >= 10
        ),

        "driver_5": int(
            top["driver_score"] >= 5
        ),

        "form_30": int(
            top["form_score"] >= 30
        ),

        "win_40": int(
            top["win_percent"] >= 40
        ),

        "place_70": int(
            top["place_percent"] >= 70
        )
    })

a = pd.DataFrame(rows)

failed = a[a["won"] == 0]
correct = a[a["won"] == 1]

print("=" * 80)
print("FELSPIKAR")
print("=" * 80)

features = [
    "post_1_6",
    "post_7_8",
    "post_9_plus",
    "field_le_10",
    "field_11_12",
    "field_13_plus",
    "gap_10",
    "gap_20",
    "gap_30",
    "latest_10",
    "driver_5",
    "form_30",
    "win_40",
    "place_70"
]

rows = []

for feature in features:

    failed_pct = round(
        failed[feature].mean() * 100,
        1
    )

    correct_pct = round(
        correct[feature].mean() * 100,
        1
    )

    diff = round(
        correct_pct - failed_pct,
        1
    )

    rows.append({
        "feature": feature,
        "felspik_%": failed_pct,
        "rättspik_%": correct_pct,
        "skillnad": diff
    })

result = pd.DataFrame(rows)

result = result.sort_values(
    "skillnad",
    ascending=False
)

print(result.to_string(index=False))