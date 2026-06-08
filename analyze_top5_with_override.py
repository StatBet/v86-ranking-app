import pandas as pd

df = pd.read_csv("ml_dataset.csv").fillna(0)

valid_races = (
    df.groupby("race_id")["won"]
    .sum()
    .reset_index()
)

valid_races = valid_races[
    valid_races["won"] == 1
]["race_id"]

df = df[
    df["race_id"].isin(valid_races)
].copy()


def apply_rank2_override(race):
    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        return race

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]

    score_gap = (
        rank1["total_score"]
        - rank2["total_score"]
    )

    if (
        rank1["post"] >= 6
        and rank2["post"] <= 8
        and score_gap < 10
    ):
        race = race.copy()

        first = race.iloc[0].copy()
        second = race.iloc[1].copy()

        race.iloc[0] = second
        race.iloc[1] = first

    return race


normal_hits = 0
override_hits = 0
both = 0
normal_only = 0
override_only = 0
neither = 0

total_races = 0

for race_id, race in df.groupby("race_id"):

    total_races += 1

    normal_ranking = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    override_ranking = apply_rank2_override(race)

    normal_top5 = set(
        normal_ranking.head(5)["horse"]
    )

    override_top5 = set(
        override_ranking.head(5)["horse"]
    )

    winner = race[
        race["won"] == 1
    ].iloc[0]["horse"]

    normal_hit = winner in normal_top5
    override_hit = winner in override_top5

    if normal_hit:
        normal_hits += 1

    if override_hit:
        override_hits += 1

    if normal_hit and override_hit:
        both += 1

    elif normal_hit and not override_hit:
        normal_only += 1

    elif not normal_hit and override_hit:
        override_only += 1

    else:
        neither += 1

print("=" * 80)
print("TOP5 MED RANK2 OVERRIDE")
print("=" * 80)

print()
print("Normal Top5")
print("----------------")
print("Träffar:", normal_hits)
print("Lopp:", total_races)
print("Träff%:", round(normal_hits / total_races * 100, 1))

print()
print("Override Top5")
print("----------------")
print("Träffar:", override_hits)
print("Lopp:", total_races)
print("Träff%:", round(override_hits / total_races * 100, 1))

print()
print("=" * 80)
print("FÖRDELNING")
print("=" * 80)

print("Both:", both)
print("Normal only:", normal_only)
print("Override only:", override_only)
print("Neither:", neither)