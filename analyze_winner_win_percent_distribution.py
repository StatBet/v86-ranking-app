import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

bins = list(range(0, 105, 5))

winners["bucket"] = pd.cut(
    winners["win_percent"],
    bins=bins,
    right=False
)

print("=" * 80)
print("WIN% FÖR ALLA VINNARE")
print("=" * 80)

result = winners["bucket"].value_counts().sort_index()

for bucket, count in result.items():
    print(f"{bucket}: {count}")