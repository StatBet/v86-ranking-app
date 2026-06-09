import pandas as pd

df = pd.read_csv("ml_dataset.csv")

# --------------------------------------------------
# Skrällvinnare
# --------------------------------------------------

skrall = df[
    (df["won"] == 1)
    & (df["percent"] <= 14)
].copy()

# --------------------------------------------------
# Top5
# --------------------------------------------------

skrall["top5"] = skrall["model_rank"] <= 5

# --------------------------------------------------
# Badge V1
# --------------------------------------------------

skrall["badge_v1"] = (
    skrall["model_rank"].between(6, 8)
    & (skrall["spike_score"] >= 170)
    & (skrall["spread"] <= 50)
    & (skrall["total_score"].between(99, 140))
)

# --------------------------------------------------
# Badge V2
# --------------------------------------------------

skrall["badge_v2"] = (
    skrall["model_rank"].between(6, 8)
    & (skrall["spike_score"] >= 120)
    & (skrall["spread"] >= 30)
    & (skrall["total_score"] >= 100)
    & (skrall["avg_odds"] <= 15)
)

# --------------------------------------------------
# Spik
# --------------------------------------------------

skrall["spik180"] = skrall["spike_score"] >= 180

# --------------------------------------------------
# Skrällprofil
# --------------------------------------------------

skrall["skrallprofil"] = (
    skrall["latest_start_score"].between(7, 10)
    & skrall["form_score"].between(19, 40)
)

# --------------------------------------------------
# Unika skrällprofilvinnare
# --------------------------------------------------

unika = skrall[
    skrall["skrallprofil"]
    & ~skrall["top5"]
    & ~skrall["badge_v1"]
    & ~skrall["badge_v2"]
    & ~skrall["spik180"]
]

print("=" * 80)
print("SKRÄLLPROFIL - UNIKA VINNARE")
print("=" * 80)

print()
print("Totala skrällvinnare:", len(skrall))
print("Skrällprofil:", int(skrall["skrallprofil"].sum()))
print("Unika skrällprofilvinnare:", len(unika))

if len(skrall):
    print(
        "Andel av alla skrällvinnare:",
        round(len(unika) / len(skrall) * 100, 1),
        "%"
    )

print()
print("=" * 80)
print("UNIKA VINNARE")
print("=" * 80)

print(
    unika[
        [
            "date",
            "race_no",
            "horse",
            "percent",
            "model_rank",
            "total_score",
            "spike_score",
            "spread",
            "form_score",
            "latest_start_score",
            "win_percent",
            "place_percent",
            "avg_odds",
            "post"
        ]
    ]
    .sort_values(
        ["percent", "model_rank"]
    )
    .to_string(index=False)
)