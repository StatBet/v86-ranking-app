import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

winners = df[df["won"] == 1].copy()

winners["place_gap"] = (
    winners["place_percent"]
    - winners["win_percent"]
)

bins = list(range(0, 105, 5))

winners["bucket"] = pd.cut(
    winners["place_gap"],
    bins=bins,
    right=False
)

print("=" * 80)
print("GAP PLACE% - WIN%")
print("=" * 80)

result = winners["bucket"].value_counts().sort_index()

for bucket, count in result.items():
    print(f"{bucket}: {count}")

print()
print("Snittgap:",
      round(winners["place_gap"].mean(), 1))