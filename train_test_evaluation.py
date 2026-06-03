import pandas as pd


DATASET_PATH = "ml_dataset.csv"

FEATURE_SETS = {
    "win_percent + form_score": [
        "win_percent",
        "form_score"
    ],
    "win_percent + form_score + avg_time": [
        "win_percent",
        "form_score",
        "avg_time"
    ],
    "avg_odds + form_score + place_percent + avg_time": [
        "avg_odds",
        "form_score",
        "place_percent",
        "avg_time"
    ],

    "+ driver_score": [
        "avg_odds",
        "form_score",
        "place_percent",
        "avg_time",
        "driver_score"
    ],

    "+ class_change_score": [
        "avg_odds",
        "form_score",
        "place_percent",
        "avg_time",
        "class_change_score"
    ],

    "+ speed_score": [
        "avg_odds",
        "form_score",
        "place_percent",
        "avg_time",
        "speed_score"
    ],

    "+ record_score": [
        "avg_odds",
        "form_score",
        "place_percent",
        "avg_time",
        "record_score"
    ],
    "win_percent + avg_time": [
        "win_percent",
        "avg_time"
    ]
}

LOWER_IS_BETTER = [
    "avg_odds",
    "avg_time"
]


def normalize_feature(df, feature):
    values = df[feature].astype(float)

    min_v = values.min()
    max_v = values.max()

    if max_v == min_v:
        return 0

    normalized = (values - min_v) / (max_v - min_v)

    if feature in LOWER_IS_BETTER:
        normalized = 1 - normalized

    return normalized * 100


def evaluate(df, score_col):
    total_races = 0
    rank_1 = 0
    top_3 = 0
    top_5 = 0
    ranks = []

    for race_id, group in df.groupby("race_id"):
        if group["won"].sum() != 1:
            continue

        total_races += 1

        ranked = group.sort_values(
            score_col,
            ascending=False
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
df = df[df["race_id"].isin(valid_races)].copy()

dates = sorted(df["date"].unique())

split_index = int(len(dates) * 0.75)

train_dates = dates[:split_index]
test_dates = dates[split_index:]

train_df = df[df["date"].isin(train_dates)].copy()
test_df = df[df["date"].isin(test_dates)].copy()

print("=" * 80)
print("TRAIN / TEST")
print("=" * 80)
print("Train datum:", train_dates[0], "till", train_dates[-1])
print("Test datum:", test_dates[0], "till", test_dates[-1])
print("Train lopp:", train_df["race_id"].nunique())
print("Test lopp:", test_df["race_id"].nunique())

results = []

for model_name, features in FEATURE_SETS.items():

    for feature in features:
        train_df[f"{feature}_norm"] = normalize_feature(train_df, feature)
        test_df[f"{feature}_norm"] = normalize_feature(test_df, feature)

    train_df["model_score"] = 0
    test_df["model_score"] = 0

    for feature in features:
        train_df["model_score"] += train_df[f"{feature}_norm"]
        test_df["model_score"] += test_df[f"{feature}_norm"]

    train_result = evaluate(train_df, "model_score")
    test_result = evaluate(test_df, "model_score")

    results.append({
        "model": model_name,
        "train_rank1": train_result["rank_1_pct"],
        "train_top3": train_result["top_3_pct"],
        "train_top5": train_result["top_5_pct"],
        "train_avg_rank": train_result["avg_rank"],
        "test_rank1": test_result["rank_1_pct"],
        "test_top3": test_result["top_3_pct"],
        "test_top5": test_result["top_5_pct"],
        "test_avg_rank": test_result["avg_rank"],
    })


result_df = pd.DataFrame(results)

result_df = result_df.sort_values(
    ["test_top5", "test_top3", "test_rank1"],
    ascending=False
)

print()
print("=" * 80)
print("RESULTAT")
print("=" * 80)
print(result_df.to_string(index=False))