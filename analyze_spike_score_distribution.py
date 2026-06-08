import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["form_score"] * 1.5
    + df["place_percent"]
)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

print("=" * 80)
print("RANK 6-8")
print("=" * 80)

for limit in [80, 100, 120, 140, 160, 180]:

    subset = rank68[
        rank68["spike_score"] >= limit
    ]

    total = len(subset)
    wins = int(subset["won"].sum())

    pct = (
        round(wins / total * 100, 1)
        if total else 0
    )

    print(
        f"Spike >= {limit}: "
        f"{wins}/{total} "
        f"({pct}%)"
    )