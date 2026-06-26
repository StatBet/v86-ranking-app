import pandas as pd

details = pd.read_csv("100k_new_signal_systems_540_details.csv")

rounds = (
    details.groupby(["profile", "date", "payout_8_value", "round_rows", "round_hits"])
    .agg(
        misses=("hit", lambda x: int((x == 0).sum())),
    )
    .reset_index()
    .sort_values(["round_hits", "payout_8_value"], ascending=[False, False])
)

print()
print("=" * 100)
print("BÄSTA OMGÅNGAR PER PROFIL")
print("=" * 100)
print(rounds.to_string(index=False))

misses = details[details["hit"] == 0].copy()

miss_summary = (
    misses.groupby(["profile", "race_type"])
    .agg(
        misses=("race_id", "count"),
        avg_winner_rank=("winner_rank", "mean"),
        avg_winner_percent=("winner_percent", "mean"),
    )
    .round(2)
    .reset_index()
    .sort_values(["profile", "misses"], ascending=[True, False])
)

print()
print("=" * 100)
print("MISSAR PER PROFIL / LOPPTYP")
print("=" * 100)
print(miss_summary.to_string(index=False))

worst_misses = misses[
    [
        "profile",
        "date",
        "payout_8_value",
        "race_no",
        "race_type",
        "wanted",
        "winner",
        "winner_rank",
        "winner_percent",
        "picked",
        "level1",
        "level2",
        "level3",
        "spik_red",
        "top3_sum",
        "round_hits",
        "round_rows",
    ]
].sort_values(
    ["profile", "round_hits", "winner_percent"],
    ascending=[True, False, True]
)

rounds.to_csv("100k_system_best_rounds_with_dates.csv", index=False, encoding="utf-8-sig")
miss_summary.to_csv("100k_system_miss_summary_by_racetype.csv", index=False, encoding="utf-8-sig")
worst_misses.to_csv("100k_system_missed_races_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("100k_system_best_rounds_with_dates.csv")
print("100k_system_miss_summary_by_racetype.csv")
print("100k_system_missed_races_details.csv")