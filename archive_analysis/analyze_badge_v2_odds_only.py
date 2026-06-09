import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

badge = rank68[
    rank68["avg_odds"] <= 15
]

print("=" * 80)
print("BADGE V2 - AVG_ODDS <= 15")
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