# analyze_skrall_profile_rank_groups.py

import pandas as pd

df = pd.read_csv("ml_dataset.csv")

profile = df[
    (df["latest_start_score"] >= 7)
    & (df["latest_start_score"] <= 10)
    & (df["form_score"] >= 19)
    & (df["form_score"] <= 40)
]

rank68 = profile[
    profile["model_rank"].between(6, 8)
]

rank915 = profile[
    profile["model_rank"].between(9, 15)
]

print("=" * 80)
print("SKRÄLLPROFIL")
print("=" * 80)

print()
print("Totalt kandidater:", len(profile))
print("Vinnare:", int(profile["won"].sum()))
print(
    "Träff%:",
    round(profile["won"].mean() * 100, 1)
)

print()
print("=" * 80)
print("RANK 6-8")
print("=" * 80)

print("Kandidater:", len(rank68))
print("Vinnare:", int(rank68["won"].sum()))
print(
    "Träff%:",
    round(rank68["won"].mean() * 100, 1)
)

print()
print("=" * 80)
print("RANK 9-15")
print("=" * 80)

print("Kandidater:", len(rank915))
print("Vinnare:", int(rank915["won"].sum()))
print(
    "Träff%:",
    round(rank915["won"].mean() * 100, 1)
)

print()
print("Skrällvinnare (spel% <=14)")
print()

rank68_skrall = rank68[
    (rank68["won"] == 1)
    & (rank68["percent"] <= 14)
]

rank915_skrall = rank915[
    (rank915["won"] == 1)
    & (rank915["percent"] <= 14)
]

print(
    "Rank 6-8:",
    len(rank68_skrall)
)

print(
    "Rank 9-15:",
    len(rank915_skrall)
)