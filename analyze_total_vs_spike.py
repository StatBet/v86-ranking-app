import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rank1 = df[df["model_rank"] == 1].copy()

for col in [
    "win_percent",
    "form_score",
    "avg_time",
    "avg_odds",
    "place_percent"
]:
    rank1[f"{col}_norm"] = (
        rank1[col]
        / rank1[col].max()
        * 100
    )

rank1["form_stability"] = 0
rank1["place_stability"] = 0
rank1["post_risk"] = 0
rank1["score_gap_bonus"] = 0
rank1["post_bonus"] = 0
rank1["field_size_penalty"] = 0
rank1["environment_score"] = 0
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
    + rank1["place_percent_norm"] * 2
    + rank1["latest_bonus"]
)

print("=" * 80)
print("TOTAL SCORE")
print("=" * 80)

for picks_per_date in [2, 3, 4]:

    selected = []

    for date, group in rank1.groupby("date"):
        selected.append(
            group.sort_values(
                "total_score",
                ascending=False
            ).head(picks_per_date)
        )

    selected = pd.concat(selected)

    print()
    print(f"{picks_per_date} spikar")

    print(
        "Rätt:",
        int(selected["won"].sum())
    )

    print(
        "Träff%:",
        round(
            selected["won"].mean() * 100,
            1
        )
    )

print()
print("=" * 80)
print("SPIKE SCORE")
print("=" * 80)

for picks_per_date in [2, 3, 4]:

    selected = []

    for date, group in rank1.groupby("date"):
        selected.append(
            group.sort_values(
                "spike_score",
                ascending=False
            ).head(picks_per_date)
        )

    selected = pd.concat(selected)

    print()
    print(f"{picks_per_date} spikar")

    print(
        "Rätt:",
        int(selected["won"].sum())
    )

    print(
        "Träff%:",
        round(
            selected["won"].mean() * 100,
            1
        )
    )