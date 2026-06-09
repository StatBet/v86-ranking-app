import pandas as pd


DATASET_PATH = "ml_dataset.csv"

FEATURES = [
    "speed_score",
    "record_score",
    "form_score",
    "latest_start_score",
    "driver_score",
    "win_percent",
    "place_percent",
    "prize_money",
    "recent_prize_score",
    "class_change_score",
    "avg_time",
    "avg_odds"
]


def evaluate_feature(df, feature):
    total_races = 0
    rank_1 = 0
    top_3 = 0
    top_5 = 0
    ranks = []

    ascending = feature in [
        "avg_time",
        "avg_odds"
    ]

    for race_id, group in df.groupby("race_id"):
        if group["won"].sum() != 1:
            continue

        total_races += 1

        ranked = group.sort_values(
            feature,
            ascending=ascending
        ).reset_index(drop=True)

        winner_index = ranked.index[ranked["won"] == 1][0]
        winner_rank = winner_index + 1

        ranks.append(winner_rank)

        if winner_rank == 1:
            rank_1 += 1

        if winner_rank <= 3:
            top_3 += 1

        if winner_rank <= 5:
            top_5 += 1

    return {
        "feature": feature,
        "races": total_races,
        "rank_1": rank_1,
        "top_3": top_3,
        "top_5": top_5,
        "rank_1_pct": round(rank_1 / total_races * 100, 1),
        "top_3_pct": round(top_3 / total_races * 100, 1),
        "top_5_pct": round(top_5 / total_races * 100, 1),
        "avg_rank": round(sum(ranks) / len(ranks), 2)
    }


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[valid_races["won"] == 1]["race_id"]
df = df[df["race_id"].isin(valid_races)]

results = []

for feature in FEATURES:
    results.append(evaluate_feature(df, feature))

result_df = pd.DataFrame(results)

result_df = result_df.sort_values(
    ["top_5_pct", "top_3_pct", "rank_1_pct"],
    ascending=False
)

print("=" * 80)
print("FEATURE STRENGTH - ENSKILDA PARAMETRAR")
print("=" * 80)

print(result_df.to_string(index=False))