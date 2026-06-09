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
        - r8.iloc[0]["total_score"]
    )

df["spread"] = df["race_id"].map(spreads)

rank68 = df[df["model_rank"].between(6, 8)].copy()

v2 = rank68[
    (rank68["spike_score"] >= 120)
    &
    (rank68["spread"] <= 50)
    &
    (rank68["total_score"] >= 105)
    &
    (rank68["avg_odds"] <= 15)
].copy()

print("=" * 80)
print("V2 POST + SPIKE FILTER")
print("=" * 80)

tests = []

for post_limit in [4, 5, 6, 7]:
    tests.append((
        f"post <= {post_limit}",
        v2[v2["post"] <= post_limit]
    ))

for post_limit in [4, 5, 6, 7]:
    tests.append((
        f"post <= {post_limit} OR spike >= 150",
        v2[
            (v2["post"] <= post_limit)
            |
            (v2["spike_score"] >= 150)
        ]
    ))

for name, subset in tests:
    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print(
        "Träff%:",
        round(subset["won"].mean() * 100, 1)
        if len(subset)
        else 0
    )

print()
print("=" * 80)
print("V2 BAS")
print("=" * 80)

print("Kandidater:", len(v2))
print("Vinnare:", int(v2["won"].sum()))
print("Träff%:", round(v2["won"].mean() * 100, 1))

print()
print("=" * 80)
print("VINNARE SOM TAPPAS PER FILTER")
print("=" * 80)

base_winners = set(
    v2[v2["won"] == 1][["date", "race_no", "horse"]]
    .apply(tuple, axis=1)
)

for name, subset in tests:
    subset_winners = set(
        subset[subset["won"] == 1][["date", "race_no", "horse"]]
        .apply(tuple, axis=1)
    )

    lost = base_winners - subset_winners

    print()
    print(name)
    print("-" * 40)
    print("Tappade vinnare:", len(lost))

    if lost:
        lost_df = v2[
            v2[["date", "race_no", "horse"]]
            .apply(tuple, axis=1)
            .isin(lost)
        ]

        print(
            lost_df[
                [
                    "date",
                    "race_no",
                    "horse",
                    "model_rank",
                    "post",
                    "spike_score",
                    "total_score",
                    "spread",
                    "avg_odds"
                ]
            ]
            .sort_values("spike_score", ascending=False)
            .to_string(index=False)
        )