import pandas as pd
from functools import reduce
from operator import mul

DATASET = "ml_dataset.csv"
MAX_ROWS = 500
MAX_HORSES_PER_RACE = 7

df = pd.read_csv(DATASET).fillna(0)

valid_dates = []

for date, g in df.groupby("date"):
    if g["race_no"].nunique() == 8 and g["won"].sum() == 8:
        valid_dates.append(date)

df = df[df["date"].isin(valid_dates)].copy()


def rows_count(picks):
    return reduce(mul, picks.values(), 1)


def apply_rank2_override(race):
    race = race.sort_values(
        "total_score",
        ascending=False
    ).reset_index(drop=True)

    if len(race) < 2:
        return race

    rank1 = race.iloc[0]
    rank2 = race.iloc[1]

    score_gap = rank1["total_score"] - rank2["total_score"]

    if (
        rank1["post"] >= 6
        and rank2["post"] <= 8
        and score_gap < 10
    ):
        race = race.copy()
        race.iloc[0], race.iloc[1] = race.iloc[1].copy(), race.iloc[0].copy()

    return race


def build_system(date_df):
    races = {}

    for race_no, race in date_df.groupby("race_no"):
        races[race_no] = apply_rank2_override(race)

    picks = {}

    # Startval baserat på hur öppet loppet är
    for race_no, race in races.items():
        if len(race) < 2:
            picks[race_no] = 1
            continue

        gap = race.iloc[0]["total_score"] - race.iloc[1]["total_score"]

        if gap >= 30:
            picks[race_no] = 1
        elif gap >= 20:
            picks[race_no] = 2
        elif gap >= 10:
            picks[race_no] = 3
        else:
            picks[race_no] = 4

        picks[race_no] = min(picks[race_no], len(race), MAX_HORSES_PER_RACE)

    # Om systemet är för stort: minska först i tydligaste loppen
    while rows_count(picks) > MAX_ROWS:
        best_race = None
        best_gap = -999

        for race_no, race in races.items():
            if picks[race_no] <= 1:
                continue

            gap = race.iloc[0]["total_score"] - race.iloc[1]["total_score"]

            if gap > best_gap:
                best_gap = gap
                best_race = race_no

        if best_race is None:
            break

        picks[best_race] -= 1

    # Om rader finns kvar: lägg till där nästa häst är starkast
    while True:
        current_rows = rows_count(picks)
        best_race = None
        best_value = -999

        for race_no, race in races.items():
            current_n = picks[race_no]

            if current_n >= min(len(race), MAX_HORSES_PER_RACE):
                continue

            new_rows = current_rows * (current_n + 1) / current_n

            if new_rows > MAX_ROWS:
                continue

            next_horse = race.iloc[current_n]

            # Värde för att gardera nästa häst
            value = (
                next_horse["total_score"]
                + next_horse["form_score"] * 1.5
                + next_horse["place_percent"]
                + next_horse["win_percent"]
            ) / current_n

            if value > best_value:
                best_value = value
                best_race = race_no

        if best_race is None:
            break

        picks[best_race] += 1

    selected = {}

    for race_no, race in races.items():
        selected[race_no] = race.head(picks[race_no])

    return selected, rows_count(picks), picks


results = []

for date, date_df in df.groupby("date"):
    selected, total_rows, picks = build_system(date_df)

    hits = 0

    for race_no, horses in selected.items():
        if horses["won"].sum() > 0:
            hits += 1

    results.append({
        "date": date,
        "rows": total_rows,
        "hits": hits,
        "system": "x".join(str(picks[r]) for r in sorted(picks))
    })

r = pd.DataFrame(results)

print("=" * 80)
print("500 RADERS SYSTEM V2")
print("=" * 80)

print("Omgångar:", len(r))
print("Snittrader:", round(r["rows"].mean(), 1))
print("8 rätt:", int((r["hits"] == 8).sum()))
print("7 rätt:", int((r["hits"] == 7).sum()))
print("6 rätt:", int((r["hits"] == 6).sum()))

print()
print("Fördelning:")
print(r["hits"].value_counts().sort_index().to_string())

print()
print("=" * 80)
print("BÄSTA OMGÅNGAR")
print("=" * 80)

print(
    r.sort_values(
        ["hits", "rows"],
        ascending=[False, True]
    )
    .head(20)
    .to_string(index=False)
)