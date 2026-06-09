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

v1 = df[
    (df["model_rank"].between(6, 8))
    & (df["spike_score"] >= 170)
    & (df["spread"] <= 51)
    & (df["total_score"].between(99, 139))
].copy()

v2_base = df[
    (df["model_rank"].between(6, 8))
    & (df["spike_score"] >= 120)
    & (df["spread"] <= 50)
    & (df["total_score"] >= 105)
    & (df["avg_odds"] <= 15)
].copy()

variants = [
    (
        "A: post <= 5 OR latest >= 10 OR form >= 30",
        v2_base[
            (v2_base["post"] <= 5)
            | (v2_base["latest_start_score"] >= 10)
            | (v2_base["form_score"] >= 30)
        ],
    ),
    (
        "B: post <= 5 OR latest >= 7 OR form >= 35",
        v2_base[
            (v2_base["post"] <= 5)
            | (v2_base["latest_start_score"] >= 7)
            | (v2_base["form_score"] >= 35)
        ],
    ),
    (
        "C: post <= 5 OR latest >= 10 OR form >= 35",
        v2_base[
            (v2_base["post"] <= 5)
            | (v2_base["latest_start_score"] >= 10)
            | (v2_base["form_score"] >= 35)
        ],
    ),
    (
        "D: post <= 4 OR latest >= 10 OR form >= 35",
        v2_base[
            (v2_base["post"] <= 4)
            | (v2_base["latest_start_score"] >= 10)
            | (v2_base["form_score"] >= 35)
        ],
    ),
]

def make_keys(frame):
    return set(
        frame[["date", "race_no", "horse"]]
        .apply(tuple, axis=1)
    )

v1_keys = make_keys(v1)

print("=" * 80)
print("V2 STRONG VARIANTER")
print("=" * 80)

print()
print("V2 BAS")
print("-" * 40)
print("Kandidater:", len(v2_base))
print("Vinnare:", int(v2_base["won"].sum()))
print("Träff%:", round(v2_base["won"].mean() * 100, 1))

print()
print("V1")
print("-" * 40)
print("Kandidater:", len(v1))
print("Vinnare:", int(v1["won"].sum()))
print("Träff%:", round(v1["won"].mean() * 100, 1))

print()
print("=" * 80)
print("VARIANTER ENSKILT")
print("=" * 80)

for name, subset in variants:
    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print("Träff%:", round(subset["won"].mean() * 100, 1) if len(subset) else 0)

print()
print("=" * 80)
print("V1 + VARIANT")
print("=" * 80)

for name, subset in variants:
    combined_keys = v1_keys | make_keys(subset)

    combined = df[
        df[["date", "race_no", "horse"]]
        .apply(tuple, axis=1)
        .isin(combined_keys)
    ]

    print()
    print("V1 + " + name)
    print("-" * 40)
    print("Kandidater:", len(combined))
    print("Vinnare:", int(combined["won"].sum()))
    print("Träff%:", round(combined["won"].mean() * 100, 1) if len(combined) else 0)

print()
print("=" * 80)
print("TAPPADE VINNARE JÄMFÖRT MED V1 + V2 BAS")
print("=" * 80)

base_combined_keys = v1_keys | make_keys(v2_base)
base_winner_keys = make_keys(
    df[
        df[["date", "race_no", "horse"]]
        .apply(tuple, axis=1)
        .isin(base_combined_keys)
        & (df["won"] == 1)
    ]
)

for name, subset in variants:
    combined_keys = v1_keys | make_keys(subset)

    winner_keys = make_keys(
        df[
            df[["date", "race_no", "horse"]]
            .apply(tuple, axis=1)
            .isin(combined_keys)
            & (df["won"] == 1)
        ]
    )

    lost = base_winner_keys - winner_keys

    print()
    print(name)
    print("-" * 40)
    print("Tappade vinnare:", len(lost))

    if lost:
        lost_df = df[
            df[["date", "race_no", "horse"]]
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
                    "latest_start_score",
                    "form_score",
                    "driver_score",
                    "win_percent",
                    "place_percent",
                    "total_score",
                    "spike_score",
                    "spread",
                    "avg_odds",
                ]
            ]
            .sort_values("spike_score", ascending=False)
            .to_string(index=False)
        )