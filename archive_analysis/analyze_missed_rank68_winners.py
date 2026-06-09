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

rank68 = df[df["model_rank"].between(6, 8)].copy()

badge = rank68[
    (rank68["spike_score"] >= 170)
    & (rank68["spread"] <= 51)
    & (rank68["total_score"].between(99, 139))
]

badge_ids = set(badge[["date", "race_no", "horse"]].apply(tuple, axis=1))

missed = rank68[rank68["won"] == 1].copy()
missed = missed[
    ~missed[["date", "race_no", "horse"]].apply(tuple, axis=1).isin(badge_ids)
]

print("=" * 80)
print("MISSADE RANK 6-8 VINNARE")
print("=" * 80)
print("Antal:", len(missed))

print()
print(
    missed[
        [
            "date", "race_no", "horse", "model_rank",
            "total_score", "spike_score", "spread",
            "win_percent", "place_percent", "form_score",
            "latest_start_score", "avg_odds", "post"
        ]
    ]
    .sort_values("spike_score", ascending=False)
    .to_string(index=False)
)