import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

filt = (
    (
        (df["model_rank"].between(6, 8))
        & (df["spike_score"] <= 120)
        & (df["driver_score"] == 0)
        & (df["latest_start_score"] <= 3)
        & (df["form_score"] <= 20)
        & (df["avg_odds"] > 15)
        & (df["speed_score"] <= 12)
        & (df["post"] >= 7)
    )
) | (
    (df["model_rank"].between(6, 8))
    & (df["spike_score"] <= 50)
    & (df["speed_score"] <= 12)
)

subset = df[filt]

print("=" * 80)
print("LOSER FILTER F")
print("=" * 80)
print()

print(f"Kandidater: {len(subset)}")
print(f"Vinnare: {int(subset['won'].sum())}")

if len(subset):
    print(f"Träff%: {subset['won'].mean()*100:.1f}")