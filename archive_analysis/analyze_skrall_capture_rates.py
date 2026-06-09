import pandas as pd

df = pd.read_csv("ml_dataset.csv")

# ==========================================
# SKRÄLLVINNARE
# ==========================================

winners = df[df["won"] == 1].copy()

skrall = winners[
    (winners["percent"] <= 14)
].copy()

# ==========================================
# BADGE V1
# ==========================================

badge_v1 = (
    (skrall["model_rank"].between(6, 8))
    & (skrall["spike_score"] >= 170)
    & (skrall["spread"] <= 50)
    & (skrall["total_score"].between(99, 140))
)

# ==========================================
# BADGE V2
# ==========================================

badge_v2 = (
    (skrall["model_rank"].between(6, 8))
    & (skrall["spike_score"] >= 120)
    & (skrall["spread"] >= 30)
    & (skrall["total_score"] >= 100)
    & (skrall["avg_odds"] <= 15)
)

# ==========================================
# TOP 5
# ==========================================

top5 = skrall["model_rank"] <= 5

# ==========================================
# SPIK
# ==========================================

spik = skrall["spike_score"] >= 180

# ==========================================
# GRUPPER
# ==========================================

groups = [
    ("0-2%", 0, 2),
    ("3-5%", 3, 5),
    ("6-9%", 6, 9),
    ("10-14%", 10, 14),
]

print("=" * 80)
print("SKRÄLLAR - VAD FÅNGAR VI REDAN?")
print("=" * 80)

for name, low, high in groups:

    grp = skrall[
        (skrall["percent"] >= low)
        & (skrall["percent"] <= high)
    ]

    total = len(grp)

    b1 = len(grp[
        (grp["model_rank"].between(6,8))
        & (grp["spike_score"] >= 170)
        & (grp["spread"] <= 50)
        & (grp["total_score"].between(99,140))
    ])

    b2 = len(grp[
        (grp["model_rank"].between(6,8))
        & (grp["spike_score"] >= 120)
        & (grp["spread"] >= 30)
        & (grp["total_score"] >= 100)
        & (grp["avg_odds"] <= 15)
    ])

    top5_hits = len(grp[grp["model_rank"] <= 5])

    spik_hits = len(grp[grp["spike_score"] >= 180])

    print()
    print(name)
    print("-" * 40)
    print(f"Vinnare: {total}")
    print(f"Top5: {top5_hits} ({top5_hits/total*100:.1f}%)")
    print(f"Badge V1: {b1} ({b1/total*100:.1f}%)")
    print(f"Badge V2: {b2} ({b2/total*100:.1f}%)")
    print(f"Spik >=180: {spik_hits} ({spik_hits/total*100:.1f}%)")

# ==========================================
# TOTALT
# ==========================================

print()
print("=" * 80)
print("TOTALT 0-14%")
print("=" * 80)

total = len(skrall)

top5_hits = len(skrall[skrall["model_rank"] <= 5])

badge_v1_hits = len(skrall[
    (skrall["model_rank"].between(6,8))
    & (skrall["spike_score"] >= 170)
    & (skrall["spread"] <= 50)
    & (skrall["total_score"].between(99,140))
])

badge_v2_hits = len(skrall[
    (skrall["model_rank"].between(6,8))
    & (skrall["spike_score"] >= 120)
    & (skrall["spread"] >= 30)
    & (skrall["total_score"] >= 100)
    & (skrall["avg_odds"] <= 15)
])

spik_hits = len(skrall[skrall["spike_score"] >= 180])

print(f"Vinnare: {total}")
print(f"Top5: {top5_hits} ({top5_hits/total*100:.1f}%)")
print(f"Badge V1: {badge_v1_hits} ({badge_v1_hits/total*100:.1f}%)")
print(f"Badge V2: {badge_v2_hits} ({badge_v2_hits/total*100:.1f}%)")
print(f"Spik >=180: {spik_hits} ({spik_hits/total*100:.1f}%)")