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

    spreads[race_id] = (
        r1.iloc[0]["total_score"]
        -
        r8.iloc[0]["total_score"]
    )

df["spread"] = df["race_id"].map(spreads)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

badge = rank68[
    (rank68["spike_score"] >= 120)
    &
    (rank68["spread"] <= 50)
    &
    (rank68["total_score"] >= 105)
    &
    (rank68["avg_odds"] <= 15)
]

print("=" * 80)
print("BADGE V2 - KOMBO")
print("=" * 80)

print()
print("Kandidater:", len(badge))
print("Vinnare:", int(badge["won"].sum()))
print(
    "Träff%:",
    round(
        badge["won"].mean() * 100,
        1
    )
)

print()
print("Rank 6-8 vinnare fångade:")
print(
    int(badge["won"].sum()),
    "/",
    len(rank68[rank68["won"] == 1])
)