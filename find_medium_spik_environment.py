import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")

df = df.merge(payout, on="date", how="left")
df = df[df["payout_8_value"] >= 100000].copy()


def is_open_lopp(race):
    scores = {
        int(r["model_rank"]): r["total_score"]
        for _, r in race.iterrows()
    }

    r1 = scores.get(1, 0)

    return (
        r1 - scores.get(8, 0) < 70
        and r1 - scores.get(3, 0) < 30
        and r1 - scores.get(4, 0) < 30
    )


rows = []

for race_id, race in df.groupby("race_id"):

    race = race.copy()

    winner = race[race["won"] == 1]
    if winner.empty:
        continue

    w = winner.iloc[0]

    race["spike_rank"] = race["spike_score"].rank(
        ascending=False,
        method="min"
    )

    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()

    open_lopp = is_open_lopp(race)

    r1 = race[race["model_rank"] == 1]
    r2 = race[race["model_rank"] == 2]

    rank1_percent = r1.iloc[0]["percent"] if len(r1) else 0
    rank1_spike = r1.iloc[0]["spike_score"] if len(r1) else 0

    score_gap_1_2 = 999
    spike_gap_1_2 = 999

    if len(r1) and len(r2):
        score_gap_1_2 = r1.iloc[0]["total_score"] - r2.iloc[0]["total_score"]
        spike_gap_1_2 = r1.iloc[0]["spike_score"] - r2.iloc[0]["spike_score"]

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    has_value = len(value) > 0

    level1 = has_value and w["spread"] < 70
    level2 = open_lopp and has_value
    level3 = open_lopp and has_value and 65 <= top3_sum < 75

    trap = has_value and (
        score_gap_1_2 < 10
        or spike_gap_1_2 < 25
        or rank1_spike < 175
    )

    candidates = race[
        race["percent"].between(15, 25)
    ].copy()

    if candidates.empty:
        continue

    candidates["medium_candidate"] = 1
    candidates["medium_winner"] = candidates["won"].astype(int)

    for _, h in candidates.iterrows():

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
                ranks = race[col].rank(
                    ascending=False,
                    method="min"
                )
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
            "top3_count": top3_count,

            "winner": w["horse"],
            "winner_rank": int(w["model_rank"]),
            "winner_percent": w["percent"],

            "open_lopp": int(open_lopp),
            "top3_warning": int(total_sum >= 1538),
            "top3_under75": int(top3_sum < 75),
            "top3_65_74": int(65 <= top3_sum < 75),
            "top3_under65": int(top3_sum < 65),

            "has_value": int(has_value),
            "level1": int(level1),
            "level2": int(level2),
            "level3": int(level3),
            "trap": int(trap),

            "rank1_percent": rank1_percent,
            "rank1_under25": int(rank1_percent < 25),
            "rank1_under30": int(rank1_percent < 30),
            "rank1_under35": int(rank1_percent < 35),

            "score_gap_1_2": score_gap_1_2,
            "spike_gap_1_2": spike_gap_1_2,
            "rank1_spike": rank1_spike,

            "top3_sum": top3_sum,
            "total_sum": total_sum,
            "spike_sum": spike_sum,
        })


cand = pd.DataFrame(rows)

tests = {
    "all_medium_15_25":
        cand.index == cand.index,

    "open_lopp":
        cand["open_lopp"] == 1,

    "top3_warning":
        cand["top3_warning"] == 1,

    "top3_under75":
        cand["top3_under75"] == 1,

    "open_top3_under75":
        (cand["open_lopp"] == 1)
        & (cand["top3_under75"] == 1),

    "open_top3_65_74":
        (cand["open_lopp"] == 1)
        & (cand["top3_65_74"] == 1),

    "level1_valuehunt":
        cand["level1"] == 1,

    "level2_scrallrisk":
        cand["level2"] == 1,

    "level3_extreme":
        cand["level3"] == 1,

    "trap_any":
        cand["trap"] == 1,

    "open_trap":
        (cand["open_lopp"] == 1)
        & (cand["trap"] == 1),

    "top3_warning_trap":
        (cand["top3_warning"] == 1)
        & (cand["trap"] == 1),

    "rank1_under25":
        cand["rank1_under25"] == 1,

    "rank1_under30":
        cand["rank1_under30"] == 1,

    "rank1_under35":
        cand["rank1_under35"] == 1,

    "open_rank1_under30":
        (cand["open_lopp"] == 1)
        & (cand["rank1_under30"] == 1),

    "top3_under75_rank1_under30":
        (cand["top3_under75"] == 1)
        & (cand["rank1_under30"] == 1),

    "open_top3_under75_rank1_under30":
        (cand["open_lopp"] == 1)
        & (cand["top3_under75"] == 1)
        & (cand["rank1_under30"] == 1),

    "level2_rank1_under30":
        (cand["level2"] == 1)
        & (cand["rank1_under30"] == 1),

    "level3_rank1_under30":
        (cand["level3"] == 1)
        & (cand["rank1_under30"] == 1),

    "rank2_5":
        cand["model_rank"].between(2, 5),

    "rank2_5_open":
        cand["model_rank"].between(2, 5)
        & (cand["open_lopp"] == 1),

    "rank2_5_top3_under75":
        cand["model_rank"].between(2, 5)
        & (cand["top3_under75"] == 1),

    "rank2_5_open_top3_under75":
        cand["model_rank"].between(2, 5)
        & (cand["open_lopp"] == 1)
        & (cand["top3_under75"] == 1),

    "rank2_5_level2":
        cand["model_rank"].between(2, 5)
        & (cand["level2"] == 1),

    "rank2_5_level3":
        cand["model_rank"].between(2, 5)
        & (cand["level3"] == 1),

    "rank2_5_top3count2":
        cand["model_rank"].between(2, 5)
        & (cand["top3_count"] >= 2),

    "rank2_5_top3count2_open":
        cand["model_rank"].between(2, 5)
        & (cand["top3_count"] >= 2)
        & (cand["open_lopp"] == 1),

    "rank2_5_top3count2_top3_under75":
        cand["model_rank"].between(2, 5)
        & (cand["top3_count"] >= 2)
        & (cand["top3_under75"] == 1),

    "rank2_5_top3count2_open_top3_under75":
        cand["model_rank"].between(2, 5)
        & (cand["top3_count"] >= 2)
        & (cand["open_lopp"] == 1)
        & (cand["top3_under75"] == 1),
}

summary_rows = []

for name, mask in tests.items():

    sub = cand[mask].copy()

    if len(sub) == 0:
        summary_rows.append({
            "environment": name,
            "candidates": 0,
            "winner_hits": 0,
            "hit_rate": 0,
            "races": 0,
            "races_with_winner": 0,
            "avg_candidates_per_race": 0,
            "avg_percent": 0,
            "avg_model_rank": 0,
            "avg_spike_rank": 0,
            "avg_total_score": 0,
            "avg_spike_score": 0,
            "avg_top3_count": 0,
            "avg_rank1_percent": 0,
            "avg_top3_sum": 0,
        })
        continue

    races = sub["race_id"].nunique()
    races_with_winner = sub[sub["won"] == 1]["race_id"].nunique()

    summary_rows.append({
        "environment": name,
        "candidates": len(sub),
        "winner_hits": int(sub["won"].sum()),
        "hit_rate": round(sub["won"].mean(), 4),
        "races": races,
        "races_with_winner": races_with_winner,
        "avg_candidates_per_race": round(len(sub) / races, 2),
        "avg_percent": round(sub["percent"].mean(), 2),
        "avg_model_rank": round(sub["model_rank"].mean(), 2),
        "avg_spike_rank": round(sub["spike_rank"].mean(), 2),
        "avg_total_score": round(sub["total_score"].mean(), 2),
        "avg_spike_score": round(sub["spike_score"].mean(), 2),
        "avg_top3_count": round(sub["top3_count"].mean(), 2),
        "avg_rank1_percent": round(sub["rank1_percent"].mean(), 2),
        "avg_top3_sum": round(sub["top3_sum"].mean(), 2),
    })


summary = pd.DataFrame(summary_rows).sort_values(
    ["winner_hits", "hit_rate"],
    ascending=False
)

print()
print("=" * 120)
print("MEDIUM SPIK ENVIRONMENT - 100K+")
print("=" * 120)
print(summary.to_string(index=False))

cand.to_csv(
    "medium_spik_environment_candidates.csv",
    index=False,
    encoding="utf-8-sig"
)

summary.to_csv(
    "medium_spik_environment_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("Sparat:")
print("medium_spik_environment_candidates.csv")
print("medium_spik_environment_summary.csv")