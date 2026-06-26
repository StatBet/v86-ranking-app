import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")

df = df.merge(payout, on="date", how="left")
df = df[df["payout_8_value"] >= 100000].copy()


def bucket_rank1(p):
    if p < 20:
        return "rank1_under20"
    if p < 25:
        return "rank1_20_24"
    if p < 30:
        return "rank1_25_29"
    if p < 35:
        return "rank1_30_34"
    if p < 40:
        return "rank1_35_39"
    return "rank1_40plus"


def bucket_top3(s):
    if s < 60:
        return "top3_under60"
    if s < 65:
        return "top3_60_64"
    if s < 70:
        return "top3_65_69"
    if s < 75:
        return "top3_70_74"
    if s < 80:
        return "top3_75_79"
    return "top3_80plus"


rows = []

for race_id, race in df.groupby("race_id"):
    race = race.copy()

    winner = race[race["won"] == 1]
    if winner.empty:
        continue

    w = winner.iloc[0]

    sorted_pct = race.sort_values("percent", ascending=False)
    rank1_percent = sorted_pct.iloc[0]["percent"]
    top2_sum = sorted_pct.head(2)["percent"].sum()
    top3_sum = sorted_pct.head(3)["percent"].sum()
    top4_sum = sorted_pct.head(4)["percent"].sum()

    medium = race[race["percent"].between(15, 25)]
    medium_rank2_5 = medium[medium["model_rank"].between(2, 5)]
    medium_rank1_5 = medium[medium["model_rank"].between(1, 5)]

    rows.append({
        "date": w["date"],
        "race_id": race_id,
        "race_no": w["race_no"],
        "payout_8_value": w["payout_8_value"],

        "winner": w["horse"],
        "winner_rank": int(w["model_rank"]),
        "winner_percent": w["percent"],
        "winner_is_medium_15_25": int(15 <= w["percent"] <= 25),

        "rank1_percent": rank1_percent,
        "rank1_bucket": bucket_rank1(rank1_percent),

        "top2_sum": top2_sum,
        "top3_sum": top3_sum,
        "top4_sum": top4_sum,
        "top3_bucket": bucket_top3(top3_sum),

        "medium_count": len(medium),
        "medium_rank1_5_count": len(medium_rank1_5),
        "medium_rank2_5_count": len(medium_rank2_5),

        "has_medium": int(len(medium) > 0),
        "has_2_medium": int(len(medium) >= 2),
        "has_3_medium": int(len(medium) >= 3),

        "has_medium_rank2_5": int(len(medium_rank2_5) > 0),
        "has_2_medium_rank2_5": int(len(medium_rank2_5) >= 2),

        "medium_horses": " | ".join(medium["horse"].tolist()),
        "medium_rank2_5_horses": " | ".join(medium_rank2_5["horse"].tolist()),
    })

races = pd.DataFrame(rows)


def summarize(name, mask):
    sub = races[mask].copy()

    if len(sub) == 0:
        return {
            "environment": name,
            "races": 0,
            "medium_winner_hits": 0,
            "medium_winner_rate": 0,
            "avg_winner_percent": 0,
            "avg_winner_rank": 0,
            "avg_rank1_percent": 0,
            "avg_top3_sum": 0,
            "avg_medium_count": 0,
            "avg_payout": 0,
        }

    return {
        "environment": name,
        "races": len(sub),
        "medium_winner_hits": int(sub["winner_is_medium_15_25"].sum()),
        "medium_winner_rate": round(sub["winner_is_medium_15_25"].mean(), 4),
        "avg_winner_percent": round(sub["winner_percent"].mean(), 2),
        "avg_winner_rank": round(sub["winner_rank"].mean(), 2),
        "avg_rank1_percent": round(sub["rank1_percent"].mean(), 2),
        "avg_top3_sum": round(sub["top3_sum"].mean(), 2),
        "avg_medium_count": round(sub["medium_count"].mean(), 2),
        "avg_payout": round(sub["payout_8_value"].mean(), 2),
    }


tests = {}

for b in sorted(races["rank1_bucket"].unique()):
    tests[f"rank1_bucket_{b}"] = races["rank1_bucket"] == b

for b in sorted(races["top3_bucket"].unique()):
    tests[f"top3_bucket_{b}"] = races["top3_bucket"] == b

tests.update({
    "has_medium": races["has_medium"] == 1,
    "has_2_medium": races["has_2_medium"] == 1,
    "has_3_medium": races["has_3_medium"] == 1,

    "has_medium_rank2_5": races["has_medium_rank2_5"] == 1,
    "has_2_medium_rank2_5": races["has_2_medium_rank2_5"] == 1,

    "rank1_under25_has_medium": (races["rank1_percent"] < 25) & (races["has_medium"] == 1),
    "rank1_under30_has_medium": (races["rank1_percent"] < 30) & (races["has_medium"] == 1),
    "rank1_under35_has_medium": (races["rank1_percent"] < 35) & (races["has_medium"] == 1),

    "top3_under70_has_medium": (races["top3_sum"] < 70) & (races["has_medium"] == 1),
    "top3_under75_has_medium": (races["top3_sum"] < 75) & (races["has_medium"] == 1),
    "top3_65_74_has_medium": (races["top3_sum"].between(65, 74.999)) & (races["has_medium"] == 1),

    "rank1_under30_top3_under75_has_medium": (
        (races["rank1_percent"] < 30)
        & (races["top3_sum"] < 75)
        & (races["has_medium"] == 1)
    ),

    "rank1_under30_top3_65_74_has_medium": (
        (races["rank1_percent"] < 30)
        & (races["top3_sum"].between(65, 74.999))
        & (races["has_medium"] == 1)
    ),

    "rank1_20_35_top3_60_80_has_medium": (
        (races["rank1_percent"].between(20, 35))
        & (races["top3_sum"].between(60, 80))
        & (races["has_medium"] == 1)
    ),

    "rank1_20_35_top3_65_80_has_medium_rank2_5": (
        (races["rank1_percent"].between(20, 35))
        & (races["top3_sum"].between(65, 80))
        & (races["has_medium_rank2_5"] == 1)
    ),

    "rank1_under30_has_2_medium": (
        (races["rank1_percent"] < 30)
        & (races["has_2_medium"] == 1)
    ),

    "top3_under75_has_2_medium": (
        (races["top3_sum"] < 75)
        & (races["has_2_medium"] == 1)
    ),

    "rank1_under30_top3_under75_has_2_medium": (
        (races["rank1_percent"] < 30)
        & (races["top3_sum"] < 75)
        & (races["has_2_medium"] == 1)
    ),
})

summary = pd.DataFrame([
    summarize(name, mask)
    for name, mask in tests.items()
])

summary = summary.sort_values(
    ["medium_winner_hits", "medium_winner_rate"],
    ascending=False
)

print()
print("=" * 120)
print("MEDIUM LOPP ENVIRONMENT - 100K+")
print("=" * 120)
print(summary.to_string(index=False))

print()
print("=" * 120)
print("MEDIUM LOPP DETAILS - VINNARE 15-25%")
print("=" * 120)
print(
    races[races["winner_is_medium_15_25"] == 1]
    .sort_values(["date", "race_no"])
    .to_string(index=False)
)

summary.to_csv("medium_lopp_environment_summary.csv", index=False, encoding="utf-8-sig")
races.to_csv("medium_lopp_environment_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("medium_lopp_environment_summary.csv")
print("medium_lopp_environment_details.csv")