import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

spreads = {}

for race_id, race in df.groupby("race_id"):
    r1 = race[race["model_rank"] == 1]
    r8 = race[race["model_rank"] == 8]

    if r1.empty or r8.empty:
        continue

    spreads[race_id] = r1.iloc[0]["total_score"] - r8.iloc[0]["total_score"]

df["spread"] = df["race_id"].map(spreads)

winners = df[df["won"] == 1].copy()

groups = [
    ("0-2%", 0, 2),
    ("3-5%", 3, 5),
    ("6-9%", 6, 9),
    ("10-14%", 10, 14),
    ("15-19%", 15, 19),
    ("20-29%", 20, 29),
    ("30%+", 30, 100),
]

cols = [
    "model_rank",
    "total_score",
    "spike_score",
    "spread",
    "win_percent",
    "place_percent",
    "form_score",
    "latest_start_score",
    "avg_odds",
    "post",
    "driver_score",
    "percent",
]

print("=" * 80)
print("VINNARE PER SPEL%-GRUPP")
print("=" * 80)

for name, low, high in groups:
    subset = winners[
        (winners["percent"] >= low)
        & (winners["percent"] <= high)
    ]

    print()
    print(name)
    print("-" * 40)
    print("Vinnare:", len(subset))
    print("Andel:", round(len(subset) / len(winners) * 100, 1), "%")

    if len(subset):
        print()
        print(subset[cols].mean().round(2).to_string())

print()
print("=" * 80)
print("SKRÄLLVINNARE 0-14%")
print("=" * 80)

skrall = winners[winners["percent"] <= 14]

print(
    skrall[
        [
            "date",
            "race_no",
            "horse",
            "percent",
            "model_rank",
            "total_score",
            "spike_score",
            "spread",
            "win_percent",
            "place_percent",
            "form_score",
            "latest_start_score",
            "avg_odds",
            "post",
            "driver_score",
        ]
    ]
    .sort_values(["percent", "model_rank"])
    .to_string(index=False)
)