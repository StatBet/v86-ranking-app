import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

groups = [
    ("1600-1700 AUTO", (1600, 1700), "auto"),
    ("1600-1700 VOLT", (1600, 1700), "volt"),
    ("2100-2200 AUTO", (2100, 2200), "auto"),
    ("2100-2200 VOLT", (2100, 2200), "volt"),
    ("2400-3200 AUTO", (2400, 3200), "auto"),
    ("2400-3200 VOLT", (2400, 3200), "volt"),
]

for name, (low, high), start in groups:

    subset = winners[
        (winners["distance"] >= low)
        & (winners["distance"] <= high)
        & (winners["start_type"] == start)
    ]

    print("=" * 80)
    print(name)
    print("=" * 80)

    print(
        subset["post"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()