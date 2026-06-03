import pandas as pd
from itertools import combinations


DATASET_PATH = "ml_dataset.csv"

FEATURES = [
    "win_percent",
    "avg_odds",
    "form_score",
    "place_percent",
    "latest_start_score",
    "avg_time"
]

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
        "rank_1_pct": round(rank_1 / total_races * 100, 1),
        "top_3_pct": round(top_3 / total_races * 100, 1),
        "top_5_pct": round(top_5 / total_races * 100, 1),
        "avg_rank": round(sum(ranks) / len(ranks), 2)
    }


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

for feature in FEATURES:
    df[f"{feature}_norm"] = normalize_feature(df, feature)

results = []

for n in range(1, len(FEATURES) + 1):
    for combo in combinations(FEATURES, n):

        df["combo_score"] = 0

        for feature in combo:
            df["combo_score"] += df[f"{feature}_norm"]

        result = evaluate(df, "combo_score")

        score = (
            result["top_5_pct"] * 2
            + result["top_3_pct"]
            + result["rank_1_pct"]
            - result["avg_rank"]
        )

        results.append({
            "features": ", ".join(combo),
            "count": len(combo),
            "score": round(score, 2),
            **result
        })

result_df = pd.DataFrame(results)

result_df = result_df.sort_values(
    "score",
    ascending=False
)

print("=" * 100)
print("BÄSTA FEATURE-KOMBINATIONER")
print("=" * 100)

print(result_df.head(30).to_string(index=False))