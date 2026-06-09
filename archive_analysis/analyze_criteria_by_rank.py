import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["criteria"] = 0
df["criteria"] += (df["win_percent"] >= 20).astype(int)
df["criteria"] += (df["place_percent"] >= 45).astype(int)
df["criteria"] += (df["form_score"] >= 20).astype(int)
df["criteria"] += (df["latest_start_score"] >= 5).astype(int)
df["criteria"] += (df["avg_odds"] <= 15).astype(int)

groups = {
    "Rank 1-5": df[df["model_rank"] <= 5],
    "Rank 6-8": df[df["model_rank"].between(6, 8)],
    "Rank 9+": df[df["model_rank"] >= 9]
}

print("=" * 80)
print("4 AV 5 KRITERIER")
print("=" * 80)

for name, subset in groups.items():

    total = len(subset)

    hits = len(
        subset[
            subset["criteria"] >= 4
        ]
    )

    pct = round(hits / total * 100, 1)

    print()
    print(name)
    print("-" * 40)
    print("Hästar:", total)
    print("Badge:", hits)
    print("Andel:", pct, "%")