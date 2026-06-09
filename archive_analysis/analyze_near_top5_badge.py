import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 8:
        continue

    rank1 = ranked[ranked["model_rank"] == 1]
    rank5 = ranked[ranked["model_rank"] == 5]
    rank8 = ranked[ranked["model_rank"] == 8]

    if len(rank1) == 0 or len(rank5) == 0 or len(rank8) == 0:
        continue

    rank1 = rank1.iloc[0]
    rank5 = rank5.iloc[0]
    rank8 = rank8.iloc[0]

    spread = rank1["total_score"] - rank8["total_score"]

    for _, horse in ranked.iterrows():

        rank = horse["model_rank"]

        if rank < 6 or rank > 8:
            continue

        gap_to_rank5 = (
            rank5["total_score"]
            - horse["total_score"]
        )

        rows.append({
            "won": horse["won"],
            "model_rank": rank,
            "spread": spread,
            "gap_to_rank5": gap_to_rank5
        })

res = pd.DataFrame(rows)

# Variant A
a = res[
    (res["model_rank"].between(6, 8))
    &
    (res["gap_to_rank5"] <= 6)
    &
    (res["spread"] <= 50)
]

# Variant B
b = res[
    (res["model_rank"].between(6, 7))
    &
    (res["gap_to_rank5"] <= 6)
    &
    (res["spread"] <= 50)
]

print("=" * 80)
print("VARIANT A")
print("=" * 80)

print("Kandidater:", len(a))
print("Vinnare:", int(a["won"].sum()))
print(
    "Träff%:",
    round(a["won"].mean() * 100, 1)
)

print()
print("=" * 80)
print("VARIANT B")
print("=" * 80)

print("Kandidater:", len(b))
print("Vinnare:", int(b["won"].sum()))
print(
    "Träff%:",
    round(b["won"].mean() * 100, 1)
)