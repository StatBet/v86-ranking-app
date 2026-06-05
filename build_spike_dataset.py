import pandas as pd


DATASET_PATH = "ml_dataset.csv"
OUTPUT_PATH = "spike_dataset.csv"


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

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

    score_gap = top["total_score"] - second["total_score"]

    rows.append({
        "date": top["date"],
        "race_id": race_id,
        "race_no": top["race_no"],
        "track": top["track"],
        "horse": top["horse"],
        "won": int(top["won"]),

        "total_score": top["total_score"],
        "score_gap": score_gap,

        "win_percent": top["win_percent"],
        "place_percent": top["place_percent"],
        "form_score": top["form_score"],
        "latest_start_score": top["latest_start_score"],
        "driver_score": top["driver_score"],
        "post_score": top["post_score"],
        "avg_time": top["avg_time"],
        "avg_odds": top["avg_odds"],
        "class_change_score": top["class_change_score"],
        "gallop_score": top["gallop_score"],

        "post": top["post"],
        "field_size": top["field_size"],

        "is_post_1_6": int(top["post"] <= 6),
        "is_post_7_8": int((top["post"] >= 7) and (top["post"] <= 8)),
        "is_post_9_plus": int(top["post"] >= 9),

        "is_field_10_or_less": int(top["field_size"] <= 10),
        "is_field_11_12": int((top["field_size"] >= 11) and (top["field_size"] <= 12)),
        "is_field_13_plus": int(top["field_size"] >= 13),

        "gap_10_plus": int(score_gap >= 10),
        "gap_20_plus": int(score_gap >= 20),
        "gap_30_plus": int(score_gap >= 30),

        "good_spike_zone": int(
            top["post"] <= 6
            and top["field_size"] <= 10
            and score_gap >= 10
        ),

        "bad_spike_zone": int(
            top["post"] >= 7
            and top["field_size"] >= 11
            and score_gap < 20
        )
    })


spike_df = pd.DataFrame(rows)

spike_df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 80)
print("SPIKE DATASET KLART")
print("=" * 80)
print("Rader:", len(spike_df))
print("Rätt:", int(spike_df["won"].sum()))
print("Träff%:", round(spike_df["won"].mean() * 100, 1))
print("Sparad som:", OUTPUT_PATH)