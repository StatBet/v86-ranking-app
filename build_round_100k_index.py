# build_round_100k_index.py
import pandas as pd

features = pd.read_csv("round_100k_potential_features.csv").fillna(0)

PROFILES = [
    {
        "name": "balanced_index",
        "level3_count": 4,
        "level2_count": 2,
        "top3_warning_count": 2,
        "open_lopp_count": 1,
        "medium_lopp_count": 1,
        "two_medium_count": 2,
        "rank1_under30_count": 2,
        "top3_under75_count": 1,
        "favorite_60plus_count": -3,
        "favorite_70plus_count": -4,
    },
    {
        "name": "medium_market_index",
        "level3_count": 3,
        "level2_count": 2,
        "top3_warning_count": 1,
        "open_lopp_count": 1,
        "medium_lopp_count": 2,
        "two_medium_count": 3,
        "rank1_under30_count": 3,
        "top3_under75_count": 2,
        "favorite_60plus_count": -2,
        "favorite_70plus_count": -4,
    },
    {
        "name": "chaos_index",
        "level3_count": 5,
        "level2_count": 3,
        "top3_warning_count": 3,
        "open_lopp_count": 2,
        "medium_lopp_count": 1,
        "two_medium_count": 1,
        "rank1_under30_count": 2,
        "top3_under75_count": 2,
        "favorite_60plus_count": -2,
        "favorite_70plus_count": -3,
    },
]


def score_round(row, weights):
    score = 0
    for col, weight in weights.items():
        if col == "name":
            continue
        score += row[col] * weight

    # Extra bonus/straff för hela omgångens marknadsform
    if row["top3_sum_avg"] < 75:
        score += 5
    elif row["top3_sum_avg"] < 78:
        score += 2
    elif row["top3_sum_avg"] >= 80:
        score -= 4

    if row["rank1_percent_sum"] < 310:
        score += 4
    elif row["rank1_percent_sum"] < 330:
        score += 2
    elif row["rank1_percent_sum"] > 350:
        score -= 4

    if row["medium_lopp_count"] >= 6:
        score += 3
    if row["two_medium_count"] >= 3:
        score += 3
    if row["rank1_under30_count"] >= 3:
        score += 4

    return score


all_rows = []
bucket_rows = []
rule_rows = []

for profile in PROFILES:
    df = features.copy()
    df["profile"] = profile["name"]
    df["round_100k_index"] = df.apply(lambda r: score_round(r, profile), axis=1)

    all_rows.append(df)

    # Bucket summary
    df["index_bucket"] = pd.cut(
        df["round_100k_index"],
        bins=[-999, 5, 10, 15, 20, 25, 30, 999],
        labels=["<=5", "6-10", "11-15", "16-20", "21-25", "26-30", "31+"],
        include_lowest=True
    )

    bucket = (
        df.groupby(["profile", "index_bucket"], observed=False)
        .agg(
            rounds=("date", "count"),
            count_100k=("is_100k", "sum"),
            avg_payout=("payout_8_value", "mean"),
            avg_winner_percent_sum=("winner_percent_sum", "mean"),
            avg_index=("round_100k_index", "mean"),
        )
        .reset_index()
    )

    bucket["precision_100k"] = (
        bucket["count_100k"] / bucket["rounds"]
    ).fillna(0).round(4)

    bucket_rows.append(bucket)

    # Threshold test
    for threshold in range(5, 41):
        kept = df[df["round_100k_index"] >= threshold]
        total_100k = df["is_100k"].sum()
        total_low = len(df) - total_100k

        kept_rounds = len(kept)
        kept_100k = int(kept["is_100k"].sum())
        kept_low = kept_rounds - kept_100k

        removed_low = total_low - kept_low
        removed_100k = total_100k - kept_100k

        rule_rows.append({
            "profile": profile["name"],
            "threshold": threshold,
            "kept_rounds": kept_rounds,
            "kept_100k": kept_100k,
            "kept_low": kept_low,
            "precision_100k": round(kept_100k / kept_rounds, 4) if kept_rounds else 0,
            "recall_100k": round(kept_100k / total_100k, 4) if total_100k else 0,
            "removed_low": int(removed_low),
            "removed_100k": int(removed_100k),
            "low_removed_rate": round(removed_low / total_low, 4) if total_low else 0,
            "avg_payout_kept": round(kept["payout_8_value"].mean(), 2) if kept_rounds else 0,
            "avg_winner_percent_sum_kept": round(kept["winner_percent_sum"].mean(), 2) if kept_rounds else 0,
        })

scored = pd.concat(all_rows, ignore_index=True)
bucket_summary = pd.concat(bucket_rows, ignore_index=True)
threshold_summary = pd.DataFrame(rule_rows)

threshold_summary = threshold_summary.sort_values(
    ["precision_100k", "recall_100k", "kept_100k"],
    ascending=False
)

print()
print("=" * 120)
print("ROUND 100K INDEX - BUCKET SUMMARY")
print("=" * 120)
print(bucket_summary.to_string(index=False))

print()
print("=" * 120)
print("ROUND 100K INDEX - BEST THRESHOLDS")
print("=" * 120)
print(threshold_summary.head(40).to_string(index=False))

print()
print("=" * 120)
print("SCORED ROUNDS")
print("=" * 120)
print(
    scored.sort_values(
        ["profile", "round_100k_index"],
        ascending=[True, False]
    )[[
        "profile",
        "date",
        "payout_8_value",
        "is_100k",
        "round_100k_index",
        "rank1_percent_sum",
        "top3_sum_avg",
        "open_lopp_count",
        "top3_warning_count",
        "level2_count",
        "level3_count",
        "medium_lopp_count",
        "two_medium_count",
        "rank1_under30_count",
        "favorite_60plus_count",
        "winner_percent_sum",
    ]].to_string(index=False)
)

scored.to_csv("round_100k_index_scored_rounds.csv", index=False, encoding="utf-8-sig")
bucket_summary.to_csv("round_100k_index_bucket_summary.csv", index=False, encoding="utf-8-sig")
threshold_summary.to_csv("round_100k_index_threshold_summary.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("round_100k_index_scored_rounds.csv")
print("round_100k_index_bucket_summary.csv")
print("round_100k_index_threshold_summary.csv")