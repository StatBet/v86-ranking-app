import pandas as pd
from math import prod

MAX_ROWS = 540

df = pd.read_csv("ml_dataset.csv").fillna(0)

payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date","payout_8_value"]].drop_duplicates("date")

df = df.merge(
    payout,
    on="date",
    how="left"
)

HIGH_DATES = (
    payout[payout["payout_8_value"] >= 100000]
    ["date"]
    .unique()
)

def is_open_lopp(race):

    scores = {
        int(r["model_rank"]): r["total_score"]
        for _, r in race.iterrows()
    }

    r1 = scores.get(1,0)

    return (
        r1 - scores.get(8,0) < 70
        and
        r1 - scores.get(3,0) < 30
        and
        r1 - scores.get(4,0) < 30
    )

def get_flags(race):

    winner = race[race["won"] == 1].iloc[0]

    top3_sum = (
        race.nlargest(3,"percent")
        ["percent"]
        .sum()
    )

    value = race[
        race["model_rank"].between(4,7)
        &
        race["total_score"].between(125,134)
        &
        (race["spike_score"] >= 105)
    ]

    has_value = len(value) > 0

    return {

        "open":
            is_open_lopp(race),

        "top3_sum":
            top3_sum,

        "level1":
            has_value and winner["spread"] < 70,

        "level2":
            has_value and is_open_lopp(race),

        "level3":
            has_value
            and is_open_lopp(race)
            and 65 <= top3_sum < 75,

        "value_horses":
            set(value["horse"].tolist())
    }

def race_type(f):

    if f["level3"]:
        return "level3"

    if f["level2"]:
        return "level2"

    if f["level1"]:
        return "level1"

    if f["open"]:
        return "open"

    return "normal"

PROFILES = [

{
"name":"forbid_open_under75",

"forbid": lambda f:
    f["open"]
    and
    f["top3_sum"] < 75

},

{
"name":"forbid_open_under70",

"forbid": lambda f:
    f["open"]
    and
    f["top3_sum"] < 70

},

{
"name":"baseline",

"forbid": lambda f: False

}

]

def horse_score(row,f):

    rank = int(row["model_rank"])

    score = 200 - rank*10

    if rank <= 5:
        score += 40

    if row["horse"] in f["value_horses"]:
        score += 80

    if f["level3"] and 6 <= rank <= 11:
        score += 50

    return score

all_results = []

for profile in PROFILES:

    rounds = []

    for date in HIGH_DATES:

        round_df = df[df["date"] == date]

        race_data = []

        for race_id,race in round_df.groupby("race_id"):

            f = get_flags(race)

            rt = race_type(f)

            race_data.append({
                "race_id":race_id,
                "race":race,
                "flags":f,
                "race_type":rt
            })

        rows_budget = []

        for rd in race_data:

            f = rd["flags"]

            if profile["forbid"](f):

                wanted = 2

            else:

                if rd["race_type"] == "level3":
                    wanted = 6

                elif rd["race_type"] == "level2":
                    wanted = 5

                elif rd["race_type"] == "level1":
                    wanted = 4

                elif rd["race_type"] == "open":
                    wanted = 1

                else:
                    wanted = 1

            rows_budget.append(wanted)

        while prod(rows_budget) > MAX_ROWS:

            idx = max(
                range(len(rows_budget)),
                key=lambda x: rows_budget[x]
            )

            if rows_budget[idx] > 1:
                rows_budget[idx] -= 1
            else:
                break

        hits = 0

        for wanted,rd in zip(rows_budget,race_data):

            race = rd["race"].copy()

            f = rd["flags"]

            race["pick"] = race.apply(
                lambda r: horse_score(r,f),
                axis=1
            )

            selected = (
                race.sort_values(
                    "pick",
                    ascending=False
                )
                .head(wanted)
            )

            winner = race[race["won"] == 1]

            if winner.iloc[0]["horse"] in selected["horse"].tolist():
                hits += 1

        rounds.append({

            "profile":
                profile["name"],

            "date":
                date,

            "hits":
                hits,

            "eight":
                int(hits >= 8),

            "seven":
                int(hits == 7),

            "six":
                int(hits == 6)

        })

    res = pd.DataFrame(rounds)

    all_results.append({

        "profile":
            profile["name"],

        "rounds":
            len(res),

        "eight_right":
            int(res["eight"].sum()),

        "seven_right":
            int(res["seven"].sum()),

        "six_right":
            int(res["six"].sum()),

        "avg_hits":
            round(res["hits"].mean(),3),

        "best_hits":
            int(res["hits"].max())

    })

summary = pd.DataFrame(all_results)

print()
print("="*100)
print("SPIK FÖRBJUDEN I OPEN+TOP3")
print("="*100)

print(
    summary.to_string(index=False)
)

summary.to_csv(
    "spik_forbidden_open_top3_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("Sparat:")
print("spik_forbidden_open_top3_summary.csv")