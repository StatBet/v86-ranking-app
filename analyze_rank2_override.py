import pandas as pd

df = pd.read_csv("ml_dataset.csv")

total_races = 0

current_hits = 0
override_hits = 0

override_count = 0

rank1_kept_and_won = 0
rank1_lost_due_to_override = 0
rank2_gained_due_to_override = 0

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        continue

    if race["won"].sum() != 1:
        continue

    total_races += 1

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]

    score_gap = (
        rank1["total_score"]
        - rank2["total_score"]
    )

    current_pick = rank1

    override = (
        rank1["post"] >= 6
        and rank2["post"] <= 8
        and score_gap < 12
        
    )

    if override:
        override_count += 1
        new_pick = rank2
    else:
        new_pick = rank1

    if rank1["won"] == 1:
        current_hits += 1

    if new_pick["won"] == 1:
        override_hits += 1

    if override:

        if rank1["won"] == 1:
            rank1_lost_due_to_override += 1

        if rank2["won"] == 1:
            rank2_gained_due_to_override += 1

    else:

        if rank1["won"] == 1:
            rank1_kept_and_won += 1

print("=" * 80)
print("RANK2 OVERRIDE")
print("=" * 80)

print("Lopp:", total_races)

print()
print("Nuvarande modell")
print("----------------")
print("Rätt:", current_hits)
print(
    "Träff%:",
    round(current_hits / total_races * 100, 1)
)

print()
print("Override-modell")
print("----------------")
print("Rätt:", override_hits)
print(
    "Träff%:",
    round(override_hits / total_races * 100, 1)
)

print()
print("Override användes")
print("-----------------")
print(override_count)

print()
print("Förlorade rätta rank1")
print("---------------------")
print(rank1_lost_due_to_override)

print()
print("Vunna rank2")
print("-----------")
print(rank2_gained_due_to_override)

print()
print("Netto")
print("-----")
print(
    rank2_gained_due_to_override
    - rank1_lost_due_to_override
)