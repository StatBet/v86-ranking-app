import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

base = df[
    (df["model_rank"].between(6, 15))
    & (df["latest_start_score"].between(7, 10))
    & (df["form_score"].between(19, 40))
].copy()

tests = []

checks = {
    "total_score": [70, 80, 90, 100, 110, 120, 130, 140],
    "speed_score": [5, 8, 10, 12, 15],
    "post_score": [5, 8, 10, 12, 15],
    "driver_score": [5, 8, 10, 12, 15],
    "win_percent": [10, 15, 20, 25, 30],
    "place_percent": [35, 40, 45, 50, 55],
    "avg_odds": [5, 10, 15, 20, 30],
    "percent": [2, 5, 9, 14],
}

for col, limits in checks.items():
    if col not in base.columns:
        continue

    for limit in limits:
        if col in ["total_score", "avg_odds", "percent"]:
            subset = base[base[col] <= limit]
            label = f"{col} <= {limit}"
        else:
            subset = base[base[col] >= limit]
            label = f"{col} >= {limit}"

        tests.append((label, subset))

print("=" * 80)
print("LATEST 7-10 + FORM 19-40 + RANK 6-15")
print("=" * 80)

print()
print("BAS")
print("-" * 40)
print("Kandidater:", len(base))
print("Vinnare:", int(base["won"].sum()))
print("Träff%:", round(base["won"].mean() * 100, 1) if len(base) else 0)

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
    res[res["candidates"] >= 20]
    .sort_values(["hit_pct", "winners"], ascending=False)
    .head(50)
    .to_string(index=False)
)

print()
print("=" * 80)
print("BÄSTA FILTER SORTERAT PÅ ANTAL VINNARE")
print("=" * 80)

print(
    res
    .sort_values(["winners", "hit_pct"], ascending=False)
    .head(50)
    .to_string(index=False)
)