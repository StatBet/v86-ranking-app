import itertools
import pandas as pd


DATASET_PATH = "ml_dataset.csv"

FEATURES = [
    "win_percent",
    "avg_odds",
    "form_score",
    "place_percent",
    "latest_start_score",
    "avg_time",

]

WEIGHTS = [0, 1, 2]


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

for feature in FEATURES:
    df[f"{feature}_norm"] = normalize_feature(df, feature)

best = None
tested = 0

print("=" * 80)
print("OPTIMERAR FEATURE-VIKTER")
print("=" * 80)

for weights in itertools.product(WEIGHTS, repeat=len(FEATURES)):
    if sum(weights) == 0:
        continue

    tested += 1

    df["optimized_score"] = 0

    for feature, weight in zip(FEATURES, weights):
        if weight == 0:
            continue

        df["optimized_score"] += df[f"{feature}_norm"] * weight

    result = evaluate(df, "optimized_score")

    score = (
        result["top_5_pct"] * 2
        + result["top_3_pct"]
        + result["rank_1_pct"]
        - result["avg_rank"]
    )

    if best is None or score > best["score"]:
        best = {
            "score": score,
            "weights": dict(zip(FEATURES, weights)),
            "result": result
        }

print("Testade kombinationer:", tested)

print()
print("=" * 80)
print("BÄSTA VIKTER")
print("=" * 80)

for feature, weight in best["weights"].items():
    if weight > 0:
        print(f"{feature}: x{weight}")

print()
print("=" * 80)
print("RESULTAT")
print("=" * 80)
print(best["result"])