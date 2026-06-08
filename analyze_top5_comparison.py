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

# =========================
# SPIKE SCORE PÅ ALLA HÄSTAR
# =========================

for feature in SPIKE_FEATURES:
    df[f"{feature}_norm"] = normalize_feature(df, feature)

df["form_stability"] = 0
df.loc[df["form_score"] >= 40, "form_stability"] = 15
df.loc[
    (df["form_score"] >= 30)
    & (df["form_score"] < 40),
    "form_stability"
] = 8
df.loc[df["form_score"] < 20, "form_stability"] = -15

df["place_stability"] = 0
df.loc[df["place_percent"] >= 80, "place_stability"] = 20
df.loc[
    (df["place_percent"] >= 70)
    & (df["place_percent"] < 80),
    "place_stability"
] = 10
df.loc[df["place_percent"] < 50, "place_stability"] = -20

df["post_risk"] = 0

df.loc[
    (df["start_type"] == "auto")
    & (df["post"].between(9, 12))
    & (df["field_size"] >= 12),
    "post_risk"
] = -80

df.loc[
    (df["start_type"] == "volt")
    & (df["post"].between(8, 15))
    & (df["field_size"] >= 12),
    "post_risk"
] = -120

df["score_gap_bonus"] = 0

df["post_bonus"] = 0
df["field_size_penalty"] = 0

df.loc[df["field_size"] >= 13, "field_size_penalty"] = -100
df.loc[df["field_size"] == 12, "field_size_penalty"] = -50

df.loc[df["post"].between(1, 3), "post_bonus"] = 60
df.loc[df["post"].between(4, 6), "post_bonus"] = 35
df.loc[df["post"].between(7, 8), "post_bonus"] = -50
df.loc[df["post"].between(9, 10), "post_bonus"] = -75
df.loc[df["post"] >= 11, "post_bonus"] = -100

df["environment_score"] = 0

df.loc[
    (df["post"] <= 6)
    & (df["field_size"] <= 10),
    "environment_score"
] += 60

df.loc[
    (df["post"] <= 6)
    & (df["field_size"] <= 12),
    "environment_score"
] += 30

df.loc[
    (df["post"] >= 7)
    & (df["field_size"] >= 11),
    "environment_score"
] -= 200

df["latest_bonus"] = 0

df.loc[
    df["latest_start_score"] >= 5,
    "latest_bonus"
] = 40

df["spike_score"] = (
    df["win_percent_norm"] * 2
    + df["form_score_norm"] * 1.5
    + df["avg_time_norm"] * 2
    + df["avg_odds_norm"] * 1.5
    + df["place_percent_norm"] * 2
    + df["form_stability"]
    + df["place_stability"]
    + df["post_risk"]
    + df["post_bonus"]
    + df["field_size_penalty"]
    + df["environment_score"]
    + df["latest_bonus"]
)

# =========================
# RANKING TOPP 5
# =========================

ranking_hits = 0
spike_hits = 0
races = 0

for race_id, race in df.groupby("race_id"):

    races += 1

    ranking_top5 = race.nsmallest(
        5,
        "model_rank"
    )

    spike_top5 = race.nlargest(
        5,
        "spike_score"
    )

    if ranking_top5["won"].sum() > 0:
        ranking_hits += 1

    if spike_top5["won"].sum() > 0:
        spike_hits += 1

print("=" * 80)
print("TOPP 5 JÄMFÖRELSE")
print("=" * 80)

print()
print("Ranking topp 5")
print("----------------")
print(f"Träffar: {ranking_hits}")
print(f"Lopp: {races}")
print(f"Träff%: {round(ranking_hits/races*100,1)}")

print()
print("Spike topp 5")
print("----------------")
print(f"Träffar: {spike_hits}")
print(f"Lopp: {races}")
print(f"Träff%: {round(spike_hits/races*100,1)}")