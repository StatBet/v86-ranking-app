import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rank68 = df[
    df["model_rank"].between(6, 8)
].copy()

winners = rank68[
    rank68["won"] == 1
]

losers = rank68[
    rank68["won"] == 0
]

print("=" * 80)
print("RANK 6-8 TOTAL_SCORE")
print("=" * 80)

print()
print("VINNARE")
print("-" * 40)

print(
    winners["total_score"]
    .describe()
    .round(2)
    .to_string()
)

print()
print("FÖRLORARE")
print("-" * 40)

print(
    losers["total_score"]
    .describe()
    .round(2)
    .to_string()
)

print()
print("=" * 80)
print("SNITT")
print("=" * 80)

print(
    "Vinnare:",
    round(
        winners["total_score"].mean(),
        2
    )
)

print(
    "Förlorare:",
    round(
        losers["total_score"].mean(),
        2
    )
)

print(
    "Skillnad:",
    round(
        winners["total_score"].mean()
        -
        losers["total_score"].mean(),
        2
    )
)

print()
print("=" * 80)
print("BUCKETS")
print("=" * 80)

bins = [0,100,110,120,130,140,150,999]

rank68["bucket"] = pd.cut(
    rank68["total_score"],
    bins=bins
)

summary = (
    rank68
    .groupby("bucket")
    .agg(
        kandidater=("won","count"),
        vinnare=("won","sum")
    )
)

summary["träff%"] = (
    summary["vinnare"]
    / summary["kandidater"]
    * 100
).round(1)

print(summary.to_string())