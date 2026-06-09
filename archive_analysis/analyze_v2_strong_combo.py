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

v2 = df[
    (df["model_rank"].between(6, 8))
    & (df["spike_score"] >= 120)
    & (df["spread"] <= 50)
    & (df["total_score"] >= 105)
    & (df["avg_odds"] <= 15)
].copy()

tests = [
    (
        "V2 + post <= 4 OR latest >= 10 OR form >= 35",
        v2[
            (v2["post"] <= 4)
            | (v2["latest_start_score"] >= 10)
            | (v2["form_score"] >= 35)
        ]
    ),
    (
        "V2 + post <= 5 OR latest >= 10 OR form >= 35",
        v2[
            (v2["post"] <= 5)
            | (v2["latest_start_score"] >= 10)
            | (v2["form_score"] >= 35)
        ]
    ),
    (
        "V2 + post <= 6 OR latest >= 10 OR form >= 35",
        v2[
            (v2["post"] <= 6)
            | (v2["latest_start_score"] >= 10)
            | (v2["form_score"] >= 35)
        ]
    ),
]

print("=" * 80)
print("V2 STARK KOMBO")
print("=" * 80)

print()
print("V2 BAS")
print("-" * 40)
print("Kandidater:", len(v2))
print("Vinnare:", int(v2["won"].sum()))
print("Träff%:", round(v2["won"].mean() * 100, 1))

for name, subset in tests:
    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print("Träff%:", round(subset["won"].mean() * 100, 1) if len(subset) else 0)

print()
print("=" * 80)
print("VINNARE PER BÄSTA KOMBO")
print("=" * 80)

best = tests[0][1]

print(
    best[best["won"] == 1][
        [
            "date",
            "race_no",
            "horse",
            "model_rank",
            "post",
            "latest_start_score",
            "form_score",
            "total_score",
            "spike_score",
            "spread",
            "avg_odds",
        ]
    ]
    .sort_values("spike_score", ascending=False)
    .to_string(index=False)
)