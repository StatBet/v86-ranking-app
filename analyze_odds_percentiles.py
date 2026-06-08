import pandas as pd

df = pd.read_csv("ml_dataset.csv")

w = df[df["won"] == 1]

print("=" * 80)
print("AVG_ODDS PERCENTILER")
print("=" * 80)

for p in [
    0.01,
    0.05,
    0.10,
    0.25,
    0.50,
    0.75,
    0.90,
    0.95,
    0.99
]:
    value = w["avg_odds"].quantile(p)

    print(
        f"{int(p*100):>2}% : {value:.2f}"
    )