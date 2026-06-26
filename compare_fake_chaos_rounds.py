import pandas as pd

INDEX_PROFILE = "balanced_index"
INDEX_THRESHOLD = 30

features = pd.read_csv("round_100k_potential_features.csv").fillna(0)
scored = pd.read_csv("round_100k_index_scored_rounds.csv").fillna(0)

idx = scored[
    (scored["profile"] == INDEX_PROFILE)
    & (scored["round_100k_index"] >= INDEX_THRESHOLD)
][["date", "round_100k_index"]]

df = features.merge(idx, on="date", how="inner")

df["group"] = df["is_100k"].apply(lambda x: "REAL_100K" if x == 1 else "FAKE_CHAOS")

numeric_cols = [
    "payout_8_value",
    "round_100k_index",
    "rank1_percent_sum",
    "rank1_percent_avg",
    "top3_sum_avg",
    "top3_sum_min",
    "top3_sum_max",
    "open_lopp_count",
    "top3_warning_count",
    "value_lopp_count",
    "level2_count",
    "level3_count",
    "medium_lopp_count",
    "two_medium_count",
    "three_medium_count",
    "rank1_under30_count",
    "rank1_under35_count",
    "top3_under75_count",
    "top3_under70_count",
    "favorite_50plus_count",
    "favorite_60plus_count",
    "favorite_70plus_count",
    "winner_percent_sum",
    "winner_percent_avg",
]

summary = (
    df.groupby("group")[numeric_cols]
    .mean()
    .round(2)
    .reset_index()
)

real = df[df["group"] == "REAL_100K"]
fake = df[df["group"] == "FAKE_CHAOS"]

diff_rows = []

for col in numeric_cols:
    real_avg = real[col].mean()
    fake_avg = fake[col].mean()

    diff_rows.append({
        "parameter": col,
        "real_100k_avg": round(real_avg, 2),
        "fake_chaos_avg": round(fake_avg, 2),
        "difference_real_minus_fake": round(real_avg - fake_avg, 2),
        "abs_difference": round(abs(real_avg - fake_avg), 2),
    })

diff = pd.DataFrame(diff_rows).sort_values("abs_difference", ascending=False)

print()
print("=" * 120)
print(f"FAKE CHAOS VS REAL 100K | {INDEX_PROFILE} >= {INDEX_THRESHOLD}")
print("=" * 120)

print()
print("ANTAL OMGÅNGAR")
print("-" * 120)
print(df["group"].value_counts().to_string())

print()
print("GRUPPMEDEL")
print("-" * 120)
print(summary.to_string(index=False))

print()
print("STÖRSTA SKILLNADER")
print("-" * 120)
print(diff.to_string(index=False))

print()
print("REAL 100K")
print("-" * 120)
print(
    real.sort_values("payout_8_value", ascending=False)[[
        "date",
        "payout_8_value",
        "round_100k_index",
        "winner_percent_sum",
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
    ]].to_string(index=False)
)

print()
print("FAKE CHAOS")
print("-" * 120)
print(
    fake.sort_values("round_100k_index", ascending=False)[[
        "date",
        "payout_8_value",
        "round_100k_index",
        "winner_percent_sum",
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
    ]].to_string(index=False)
)

summary.to_csv("fake_chaos_vs_real_100k_group_summary.csv", index=False, encoding="utf-8-sig")
diff.to_csv("fake_chaos_vs_real_100k_differences.csv", index=False, encoding="utf-8-sig")
df.to_csv("fake_chaos_vs_real_100k_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("fake_chaos_vs_real_100k_group_summary.csv")
print("fake_chaos_vs_real_100k_differences.csv")
print("fake_chaos_vs_real_100k_details.csv")