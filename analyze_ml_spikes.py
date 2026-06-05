import pandas as pd


DATASET_PATH = "ml_dataset.csv"


SPIKE_FEATURES = [
    "win_percent",
    "form_score",
    "avg_time",
    "avg_odds",
    "place_percent"
]


LOWER_IS_BETTER = [
    "avg_time",
    "avg_odds"
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


df = pd.read_csv(DATASET_PATH)
df = df.fillna(0)

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[valid_races["won"] == 1]["race_id"]
df = df[df["race_id"].isin(valid_races)].copy()

# Välj spikkandidat per lopp:
# normalt rank 1, men rank 2 om override-regeln slår in
candidate_rows = []

for race_id, race in df.groupby("race_id"):
    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 1:
        continue

    best_horse = race.iloc[0].copy()

    if len(race) > 1:
        rank1_horse = race.iloc[0]
        rank2_horse = race.iloc[1]

        score_gap = (
            rank1_horse["total_score"]
            - rank2_horse["total_score"]
        )

        if (
            rank1_horse["post"] >= 6
            and rank2_horse["post"] <= 8
            and score_gap < 10
        ):
            best_horse = rank2_horse.copy()

        best_horse["score_gap_to_top"] = score_gap

    candidate_rows.append(best_horse)

rank1 = pd.DataFrame(candidate_rows)

for feature in SPIKE_FEATURES:
    rank1[f"{feature}_norm"] = normalize_feature(rank1, feature)

rank1["form_stability"] = 0

rank1.loc[rank1["form_score"] >= 40, "form_stability"] = 15
rank1.loc[
    (rank1["form_score"] >= 30) &
    (rank1["form_score"] < 40),
    "form_stability"
] = 8

rank1.loc[rank1["form_score"] < 20, "form_stability"] = -15

rank1["place_stability"] = 0

rank1.loc[rank1["place_percent"] >= 80, "place_stability"] = 20
rank1.loc[
    (rank1["place_percent"] >= 70) &
    (rank1["place_percent"] < 80),
    "place_stability"
] = 10

rank1.loc[rank1["place_percent"] < 50, "place_stability"] = -20

rank1["post_risk"] = 0

rank1.loc[
    (rank1["start_type"] == "auto") &
    (rank1["post"].between(9, 12)) &
    (rank1["field_size"] >= 12),
    "post_risk"
] = -80

rank1.loc[
    (rank1["start_type"] == "volt") &
    (rank1["post"].between(8, 15)) &
    (rank1["field_size"] >= 12),
    "post_risk"
] = -120

rank1["score_gap_bonus"] = 0

rank1.loc[rank1["score_gap_to_top"] >= 10, "score_gap_bonus"] = 10
rank1.loc[rank1["score_gap_to_top"] >= 20, "score_gap_bonus"] = 20
rank1.loc[rank1["score_gap_to_top"] >= 25, "score_gap_bonus"] = 30
rank1.loc[rank1["score_gap_to_top"] >= 30, "score_gap_bonus"] = 40
rank1["post_bonus"] = 0
rank1["field_size_penalty"] = 0

rank1.loc[rank1["field_size"] >= 13, "field_size_penalty"] = -100
rank1.loc[rank1["field_size"] == 12, "field_size_penalty"] = -50

rank1.loc[rank1["post"].between(1, 3), "post_bonus"] = 60
rank1.loc[rank1["post"].between(4, 6), "post_bonus"] = 35
rank1.loc[rank1["post"].between(7, 8), "post_bonus"] = -50
rank1.loc[rank1["post"].between(9, 10), "post_bonus"] = -75
rank1.loc[rank1["post"] >= 11, "post_bonus"] = -100

rank1["environment_score"] = 0

# Bonuszon: bra spår + mindre fält + tydligt gap
rank1.loc[
    (rank1["post"] <= 6) &
    (rank1["field_size"] <= 10) &
    (rank1["score_gap_to_top"] >= 10),
    "environment_score"
] += 60

# Miljözon: okej/gynnsam miljö
rank1.loc[
    (rank1["post"] <= 6) &
    (rank1["field_size"] <= 12) &
    (rank1["score_gap_to_top"] >= 10),
    "environment_score"
] += 30

# Varningszon: sämre spår + större fält + inget stort gap
rank1.loc[
    (rank1["post"] >= 7) &
    (rank1["field_size"] >= 11) &
    (rank1["score_gap_to_top"] < 20),
    "environment_score"
] -= 200

rank1["latest_bonus"] = 0

rank1.loc[
    rank1["latest_start_score"] >= 5,
    "latest_bonus"
] = 40

rank1["spike_score"] = (
    rank1["win_percent_norm"] * 2
    + rank1["form_score_norm"] * 1.5
    + rank1["avg_time_norm"] * 2
    + rank1["avg_odds_norm"] * 1.5
    + rank1["place_percent_norm"] * 1
    + rank1["place_percent_norm"] * 1
    + rank1["form_stability"]
    + rank1["place_stability"]
    + rank1["post_risk"]
    + rank1["score_gap_bonus"]
    + rank1["post_bonus"]
    + rank1["field_size_penalty"]
    + rank1["environment_score"]
    + rank1["latest_bonus"]
    
    )

print("=" * 80)
print("SPIKANALYS - 2/3/4 SPIKAR PER OMGÅNG")
print("=" * 80)

for picks_per_date in [2, 3, 4]:

    selected_rows = []

    for date, group in rank1.groupby("date"):

        picks = group.sort_values(
            "spike_score",
            ascending=False
        ).head(picks_per_date)

        selected_rows.append(picks)

        selected = pd.concat(selected_rows)
        cols = [
        "horse",
        "spike_score",
        "win_percent",
        "place_percent",
        "form_score",
        "avg_odds",
        "latest_start_score",
        "environment_score",
        "score_gap_bonus"
    ]

    print(
        selected[cols]
        .sort_values("spike_score", ascending=False)
        .head(20)
        .to_string(index=False)
    )

    print()
    print("=" * 80)
    print("TOPP SPIKAR")
    print("=" * 80)

    cols = [
        "date",
        "race_no",
        "horse",
        "spike_score",
        "won"
    ]

    print(
        selected[cols]
        .sort_values(
            "spike_score",
            ascending=False
        )
        .head(30)
        .to_string(index=False)
    )

    total = len(selected)
    wins = int(selected["won"].sum())
    pct = round(wins / total * 100, 1) if total else 0

    print()
    print(f"{picks_per_date} spikar/omgång")
    print(f"Spikar: {total}")
    print(f"Rätt: {wins}")
    print(f"Träff%: {pct}")


print()
print("=" * 80)
print("DETALJER - 3 SPIKAR PER OMGÅNG")
print("=" * 80)

details = []

for date, group in rank1.groupby("date"):

    picks = group.sort_values(
        "spike_score",
        ascending=False
    ).head(3)

    for _, row in picks.iterrows():
        details.append({
            "date": row["date"],
            "race_no": row["race_no"],
            "horse": row["horse"],
            "winner": row["winner"],
            "won": row["won"],
            "spike_score": round(row["spike_score"], 2),
            "total_score": row["total_score"],
            "win_percent": row["win_percent"],
            "form_score": row["form_score"],
            "avg_time": row["avg_time"],
            "avg_odds": row["avg_odds"],
            "place_percent": row["place_percent"],
            "gallop_score": row["gallop_score"],
        })

details_df = pd.DataFrame(details)

print(details_df.to_string(index=False))