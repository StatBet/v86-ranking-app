import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)
payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")
df = df.merge(payout, on="date", how="left")

df = df[df["payout_8_value"] >= 100000].copy()
df = df[(df["percent"] >= 15) & (df["percent"] <= 25)].copy()

rows = []

for race_id, race in df.groupby("race_id"):
    race = race.copy()
    race["spike_rank"] = race["spike_score"].rank(ascending=False, method="min")
    race["score_gap_to_rank1"] = race["total_score"].max() - race["total_score"]
    race["spike_gap_to_rank1"] = race["spike_score"].max() - race["spike_score"]

    for _, h in race.iterrows():
        top3_count = 0

        for col in [
            "speed_score",
            "record_score",
            "form_score",
            "latest_start_score",
            "driver_score",
            "win_score",
            "place_score",
            "starts_score",
        ]:
            if col in race.columns:
                ranks = race[col].rank(ascending=False, method="min")
                if ranks.loc[h.name] <= 3:
                    top3_count += 1

        rows.append({
            "date": h["date"],
            "race_id": race_id,
            "race_no": h["race_no"],
            "horse": h["horse"],
            "won": int(h["won"]),
            "payout_8_value": h["payout_8_value"],
            "percent": h["percent"],
            "model_rank": int(h["model_rank"]),
            "spike_rank": int(h["spike_rank"]),
            "total_score": h["total_score"],
            "spike_score": h["spike_score"],
            "score_gap_to_rank1": h["score_gap_to_rank1"],
            "spike_gap_to_rank1": h["spike_gap_to_rank1"],
            "speed_score": h["speed_score"],
            "form_score": h["form_score"],
            "latest_start_score": h["latest_start_score"],
            "driver_score": h["driver_score"],
            "win_score": h["win_score"],
            "place_score": h["place_score"],
            "avg_odds": h["avg_odds"],
            "post": h["post"],
            "field_size": h["field_size"],
            "top3_count": top3_count,
        })

res = pd.DataFrame(rows)

compare_cols = [
    "percent",
    "model_rank",
    "spike_rank",
    "total_score",
    "spike_score",
    "score_gap_to_rank1",
    "spike_gap_to_rank1",
    "speed_score",
    "form_score",
    "latest_start_score",
    "driver_score",
    "win_score",
    "place_score",
    "avg_odds",
    "post",
    "field_size",
    "top3_count",
]

summary_rows = []

for col in compare_cols:
    winners = res[res["won"] == 1][col]
    losers = res[res["won"] == 0][col]

    summary_rows.append({
        "parameter": col,
        "winner_avg": round(winners.mean(), 2),
        "loser_avg": round(losers.mean(), 2),
        "difference": round(winners.mean() - losers.mean(), 2),
        "winner_median": round(winners.median(), 2),
        "loser_median": round(losers.median(), 2),
    })

summary = pd.DataFrame(summary_rows)
summary["abs_difference"] = summary["difference"].abs()
summary = summary.sort_values("abs_difference", ascending=False)

print()
print("=" * 100)
print("100K+ 15-25% VINNARE VS FÖRLORARE")
print("=" * 100)
print(summary.to_string(index=False))

res.to_csv("100k_medium_percent_all_candidates.csv", index=False, encoding="utf-8-sig")
summary.to_csv("100k_medium_percent_winners_vs_losers.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("100k_medium_percent_all_candidates.csv")
print("100k_medium_percent_winners_vs_losers.csv")