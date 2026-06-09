import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

base = df[
    (df["latest_start_score"].between(7, 10))
    & (df["form_score"].between(19, 40))
].copy()

tests = []

checks = {
    "speed_score": [5, 8, 10, 12, 15],
    "post_score": [5, 8, 10, 12, 15],
    "driver_score": [5, 8, 10, 12, 15],
    "win_percent": [10, 15, 20, 25, 30],
    "place_percent": [35, 40, 45, 50, 55],
    "avg_odds": [5, 10, 15, 20, 30],
    "total_score": [90, 100, 110, 120, 130],
    "model_rank": [5, 8, 10, 12, 15],
    "percent": [2, 5, 9, 14],
}

for col, limits in checks.items():
    if col not in base.columns:
        continue

    for limit in limits:
        if col in ["avg_odds", "model_rank", "percent"]:
            subset = base[base[col] <= limit]
            label = f"{col} <= {limit}"
        else:
            subset = base[base[col] >= limit]
            label = f"{col} >= {limit}"

        tests.append((label, subset))

print("=" * 80)
print("LATEST 7-10 + FORM 19-40 + EXTRA FILTER")
print("=" * 80)

print()
print("BAS")
print("-" * 40)
print("Kandidater:", len(base))
print("Vinnare:", int(base["won"].sum()))
print("Träff%:", round(base["won"].mean() * 100, 1))

results = []

for label, subset in tests:
    candidates = len(subset)
    winners = int(subset["won"].sum())
    pct = round(subset["won"].mean() * 100, 1) if candidates else 0

    results.append({
        "filter": label,
        "candidates": candidates,
        "winners": winners,
        "hit_pct": pct
    })

res = pd.DataFrame(results)

print()
print("=" * 80)
print("BÄSTA FILTER SORTERAT PÅ TRÄFF%")
print("=" * 80)

print(
    res[
        res["candidates"] >= 20
    ]
    .sort_values(["hit_pct", "winners"], ascending=False)
    .head(40)
    .to_string(index=False)
)

print()
print("=" * 80)
print("BÄSTA FILTER SORTERAT PÅ ANTAL VINNARE")
print("=" * 80)

print(
    res
    .sort_values(["winners", "hit_pct"], ascending=False)
    .head(40)
    .to_string(index=False)
)