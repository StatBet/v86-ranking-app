import pandas as pd

df = pd.read_csv("ml_dataset.csv")

rows = []

for race_id, race in df.groupby("race_id"):

    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if race["won"].sum() != 1:
        continue

    spike = race.iloc[0]
    winner = race[race["won"] == 1].iloc[0]

    if spike["won"] == 1:
        continue

    rows.append({
        "spike_class": spike["class_change_score"],
        "winner_class": winner["class_change_score"],

        "spike_form": spike["form_score"],
        "winner_form": winner["form_score"],

        "spike_win": spike["win_percent"],
        "winner_win": winner["win_percent"],

        "winner_better_class": int(
            winner["class_change_score"]
            > spike["class_change_score"]
        ),

        "class_diff": (
            winner["class_change_score"]
            - spike["class_change_score"]
        )
    })

a = pd.DataFrame(rows)

print("=" * 80)
print("CLASS CHANGE")
print("=" * 80)

print("Felspikar:", len(a))

print()
print("Snitt class_change_score")
print("------------------------")

print(
    pd.Series({
        "Spike": round(a["spike_class"].mean(), 2),
        "Winner": round(a["winner_class"].mean(), 2)
    })
)

print()
print("Vinnaren hade bättre class_change_score")
print("---------------------------------------")

print(
    round(
        a["winner_better_class"].mean() * 100,
        1
    ),
    "%"
)

print()
print("Genomsnittlig skillnad")
print("----------------------")

print(
    round(
        a["class_diff"].mean(),
        2
    )
)

print()
print("=" * 80)
print("STÖRSTA KLASSMISSAR")
print("=" * 80)

print(
    a.sort_values(
        "class_diff",
        ascending=False
    )
    .head(25)
    .to_string(index=False)
)