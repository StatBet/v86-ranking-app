import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

race_spread = {}

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 8:
        continue

    rank1 = ranked[ranked["model_rank"] == 1]
    rank8 = ranked[ranked["model_rank"] == 8]

    if len(rank1) == 0 or len(rank8) == 0:
        continue

    spread = (
        rank1.iloc[0]["total_score"]
        - rank8.iloc[0]["total_score"]
    )

    race_spread[race_id] = spread

df["spread"] = df["race_id"].map(race_spread)

subset = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spread"] <= 51)
    &
    (df["spike_score"] >= 170)
    &
    (df["total_score"] >= 99)
    &
    (df["total_score"] <= 139)
].copy()

print("=" * 80)
print("SPIKE 170 + LÅG SPREAD + SCORE 99-140")
print("=" * 80)

print()
print("Kandidater:", len(subset))
print("Vinnare:", int(subset["won"].sum()))

if len(subset):
    print("Träff%:", round(subset["won"].mean() * 100, 1))

print()
print("=" * 80)
print("VINNARE")
print("=" * 80)

print(
    subset[subset["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "total_score",
            "spike_score",
            "spread",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "post"
        ]
    ]
    .sort_values(["date", "race_no"])
    .to_string(index=False)
)

print()
print("=" * 80)
print("BORTFILTRERADE FRÅN SPIKE170/LÅG SPREAD")
print("=" * 80)

base = df[
    (df["model_rank"].between(6, 8))
    &
    (df["spread"] <= 51)
    &
    (df["spike_score"] >= 170)
].copy()

removed = base[
    ~(
        (base["total_score"] >= 99)
        &
        (base["total_score"] <= 139)
    )
]

print()
print("Bortfiltrerade:", len(removed))
print("Bortfiltrerade vinnare:", int(removed["won"].sum()))

print()
print(
    removed[
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "won",
            "total_score",
            "spike_score",
            "spread",
            "avg_odds"
        ]
    ]
    .sort_values(["won", "total_score"], ascending=[False, True])
    .to_string(index=False)
)