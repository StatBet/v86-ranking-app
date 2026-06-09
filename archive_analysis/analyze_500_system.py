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


def normalize(s):
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min()) * 100


df["total_norm"] = normalize(df["total_score"])
df["spike_like_score"] = (
    normalize(df["win_percent"]) * 2
    + normalize(df["place_percent"]) * 2
    + normalize(df["form_score"]) * 1.5
    + normalize(30 - df["avg_time"]) * 2
    + normalize(20 - df["avg_odds"]) * 1.5
)

df["hybrid_score"] = (
    df["total_norm"] * 0.65
    + normalize(df["spike_like_score"]) * 0.35
)


def build_system(date_df, score_col):
    picks = {}

    races = {
        race_no: race.sort_values(score_col, ascending=False).reset_index(drop=True)
        for race_no, race in date_df.groupby("race_no")
    }

    for race_no in races:
        picks[race_no] = 1

    def rows_count():
        return reduce(mul, picks.values(), 1)

    while True:
        best_race = None
        best_value = -999

        current_rows = rows_count()

        for race_no, race in races.items():
            current_n = picks[race_no]

            if current_n >= min(MAX_HORSES_PER_RACE, len(race)):
                continue

            new_rows = current_rows * (current_n + 1) / current_n

            if new_rows > MAX_ROWS:
                continue

            next_score = race.iloc[current_n][score_col]
            value = next_score * current_n

            if value > best_value:
                best_value = value
                best_race = race_no

        if best_race is None:
            break

        picks[best_race] += 1

    selected = {}

    for race_no, race in races.items():
        selected[race_no] = race.head(picks[race_no])

    return selected, rows_count()


def evaluate(score_col):
    results = []

    for date, date_df in df.groupby("date"):
        selected, rows_count = build_system(date_df, score_col)

        hits = 0

        for race_no, picks in selected.items():
            if picks["won"].sum() > 0:
                hits += 1

        results.append({
            "date": date,
            "rows": rows_count,
            "hits": hits
        })

    r = pd.DataFrame(results)

    print()
    print("=" * 80)
    print(score_col.upper())
    print("=" * 80)

    print("Omgångar:", len(r))
    print("Snittrader:", round(r["rows"].mean(), 1))
    print("8 rätt:", int((r["hits"] == 8).sum()))
    print("7 rätt:", int((r["hits"] == 7).sum()))
    print("6 rätt:", int((r["hits"] == 6).sum()))
    print()
    print(r["hits"].value_counts().sort_index().to_string())


evaluate("total_score")
evaluate("spike_like_score")
evaluate("hybrid_score")