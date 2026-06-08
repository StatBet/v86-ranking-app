import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

rows = []

for race_id, race in df.groupby("race_id"):

    ranked = race.sort_values("model_rank")

    if len(ranked) < 2:
        continue

    fav = ranked[ranked["model_rank"] == 1]

    if len(fav) == 0:
        continue

    fav = fav.iloc[0]

    second = ranked[ranked["model_rank"] == 2]

    if len(second) == 0:
        continue

    second = second.iloc[0]

    gap = fav["total_score"] - second["total_score"]

    rows.append({
        "won": fav["won"],
        "post": fav["post"],
        "total_score": fav["total_score"],
        "gap_to_2": gap
    })

res = pd.DataFrame(rows)

res["is_tillagg"] = res["post"].isin(
    [6,7,8,9,10,11,12,13,14,15]
)

normal = res[~res["is_tillagg"]]
tillagg = res[res["is_tillagg"]]

print("=" * 80)
print("FAVORITER")
print("=" * 80)

for name, subset in [
    ("Utan tillägg", normal),
    ("Med tillägg", tillagg)
]:

    print()
    print(name)
    print("-" * 40)

    print(
        "Träff%:",
        round(
            subset["won"].mean() * 100,
            1
        )
    )

    print(
        "Snitt score:",
        round(
            subset["total_score"].mean(),
            1
        )
    )

    print(
        "Gap till tvåan:",
        round(
            subset["gap_to_2"].mean(),
            1
        )
    )

print()
print("=" * 80)
print("VINNANDE FAVORITER")
print("=" * 80)

for name, subset in [
    ("Utan tillägg", normal[normal["won"] == 1]),
    ("Med tillägg", tillagg[tillagg["won"] == 1])
]:

    print()
    print(name)
    print("-" * 40)

    print(
        "Snitt score:",
        round(
            subset["total_score"].mean(),
            1
        )
    )

    print(
        "Gap till tvåan:",
        round(
            subset["gap_to_2"].mean(),
            1
        )
    )

print()
print("=" * 80)
print("FÖRLORANDE FAVORITER")
print("=" * 80)

for name, subset in [
    ("Utan tillägg", normal[normal["won"] == 0]),
    ("Med tillägg", tillagg[tillagg["won"] == 0])
]:

    print()
    print(name)
    print("-" * 40)

    print(
        "Snitt score:",
        round(
            subset["total_score"].mean(),
            1
        )
    )

    print(
        "Gap till tvåan:",
        round(
            subset["gap_to_2"].mean(),
            1
        )
    )