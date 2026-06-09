import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

df["spike_score"] = (
    df["win_percent"] * 2
    + df["place_percent"]
    + df["form_score"] * 1.5
)

spreads = {}

for race_id, race in df.groupby("race_id"):
    r1 = race[race["model_rank"] == 1]
    r8 = race[race["model_rank"] == 8]

    if r1.empty or r8.empty:
        continue

    spreads[race_id] = r1.iloc[0]["total_score"] - r8.iloc[0]["total_score"]

df["spread"] = df["race_id"].map(spreads)

v2 = df[
    (df["model_rank"].between(6, 8))
    & (df["spike_score"] >= 120)
    & (df["spread"] <= 50)
    & (df["total_score"] >= 105)
    & (df["avg_odds"] <= 15)
].copy()

print("=" * 80)
print("V2 BAS")
print("=" * 80)
print("Kandidater:", len(v2))
print("Vinnare:", int(v2["won"].sum()))
print("Träff%:", round(v2["won"].mean() * 100, 1))
print()

tests = []

for x in [20, 25, 30, 35, 40]:
    tests.append((f"Win% >= {x}", v2[v2["win_percent"] >= x]))

for x in [45, 50, 55, 60, 65, 70]:
    tests.append((f"Place% >= {x}", v2[v2["place_percent"] >= x]))

for x in [20, 25, 30, 35, 40]:
    tests.append((f"Form >= {x}", v2[v2["form_score"] >= x]))

for x in [3, 5, 7, 10]:
    tests.append((f"Latest >= {x}", v2[v2["latest_start_score"] >= x]))

for x in [4, 5, 6, 7]:
    tests.append((f"Post <= {x}", v2[v2["post"] <= x]))

for x in [5, 8, 10, 12, 15]:
    tests.append((f"Driver >= {x}", v2[v2["driver_score"] >= x]))

for x in [0, 5, 10, 12, 15]:
    tests.append((f"Driver change >= {x}", v2[v2["driver_change_score"] >= x]))

print("=" * 80)
print("FILTERTEST")
print("=" * 80)

for name, subset in tests:
    print()
    print(name)
    print("-" * 40)
    print("Kandidater:", len(subset))
    print("Vinnare:", int(subset["won"].sum()))
    print("Träff%:", round(subset["won"].mean() * 100, 1) if len(subset) else 0)