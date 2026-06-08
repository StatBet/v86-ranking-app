import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

rank68["criteria"] = 0

rank68["criteria"] += (
    rank68["win_percent"] >= 20
).astype(int)

rank68["criteria"] += (
    rank68["place_percent"] >= 40
).astype(int)

rank68["criteria"] += (
    rank68["form_score"] >= 15
).astype(int)

rank68["criteria"] += (
    rank68["latest_start_score"] >= 5
).astype(int)

rank68["criteria"] += (
    rank68["avg_odds"] <= 10
).astype(int)

print("=" * 80)
print("UNDERSKATTAD HÄST")
print("=" * 80)

for needed in [3, 4, 5]:

    subset = rank68[
        rank68["criteria"] >= needed
    ]

    total = len(subset)

    wins = int(
        subset["won"].sum()
    )

    pct = (
        round(
            wins / total * 100,
            1
        )
        if total else 0
    )

    print()
    print(f"{needed} av 5")
    print("-" * 40)
    print("Kandidater:", total)
    print("Vinnare:", wins)
    print("Träff%:", pct)

print()
print("=" * 80)
print("5 AV 5 VINNARE")
print("=" * 80)

winners = rank68[
    (rank68["criteria"] == 5)
    &
    (rank68["won"] == 1)
]

if len(winners):

    print(
        winners[
            [
                "date",
                "race_no",
                "horse",
                "model_rank",
                "avg_odds",
                "win_percent",
                "place_percent",
                "form_score",
                "latest_start_score"
            ]
        ]
        .to_string(index=False)
    )