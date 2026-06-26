import pandas as pd
from math import prod

MAX_ROWS = 540

df = pd.read_csv("ml_dataset.csv").fillna(0)
payout = pd.read_csv("payout_vs_winner_percent_rounds.csv")
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")
df = df.merge(payout, on="date", how="left")


def is_open_lopp(race):
    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)
    return (
        r1 - scores.get(8, 0) < 70
        and r1 - scores.get(3, 0) < 30
        and r1 - scores.get(4, 0) < 30
    )


def flags(race):
    w = race[race["won"] == 1].iloc[0]
    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()
    open_lopp = is_open_lopp(race)

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    has_value = len(value) > 0

    return {
        "open": open_lopp,
        "top3_sum": top3_sum,
        "top3_warning": total_sum >= 1538,
        "compact": total_sum <= 1165 or spike_sum <= 1097,
        "has_value": has_value,
        "value_horses": set(value["horse"].tolist()),
        "level1": has_value and w["spread"] < 70,
        "level2": open_lopp and has_value,
        "level3": open_lopp and has_value and 65 <= top3_sum < 75,
        "no_spik_65_69": open_lopp and 65 <= top3_sum < 70,
        "no_spik_65_74": open_lopp and 65 <= top3_sum < 75,
        "no_spik_under70": open_lopp and top3_sum < 70,
        "no_spik_under75": open_lopp and top3_sum < 75,
    }


def race_type(f):
    if f["level3"]:
        return "level3"
    if f["level2"]:
        return "level2"
    if f["level1"]:
        return "level1"
    if f["top3_warning"]:
        return "top3"
    if f["open"]:
        return "open"
    if f["compact"]:
        return "compact"
    return "normal"


def horse_score(row, f):
    rank = int(row["model_rank"])
    horse = row["horse"]
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])

    p = 200 - rank * 10

    if rank == 1:
        p += 80
    elif rank == 2:
        p += 55
    elif rank == 3:
        p += 38
    elif rank <= 5:
        p += 20

    if horse in f["value_horses"]:
        p += 90

    if f["level2"] and 5 <= rank <= 9:
        p += 30

    if f["level3"] and 6 <= rank <= 11:
        p += 50

    if f["top3_warning"] and 5 <= rank <= 10:
        p += 18

    if pct <= 10:
        p += 10

    if spike >= 150:
        p += 10

    if score >= 120:
        p += 5

    return p


PROFILES = [
    {
        "name": "base_no_spik_none",
        "no_spik_flag": None,
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "no_spik_open_top3_65_69",
        "no_spik_flag": "no_spik_65_69",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "no_spik_open_top3_65_74",
        "no_spik_flag": "no_spik_65_74",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "no_spik_open_top3_under70",
        "no_spik_flag": "no_spik_under70",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "no_spik_open_top3_under75",
        "no_spik_flag": "no_spik_under75",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
]


def trim(data):
    priority = {
        "normal": 1,
        "compact": 2,
        "open": 3,
        "level1": 4,
        "top3": 5,
        "level2": 6,
        "level3": 7,
    }

    while prod([x["wanted"] for x in data]) > MAX_ROWS:
        candidates = [x for x in data if x["wanted"] > 1]
        if not candidates:
            break

        c = sorted(candidates, key=lambda x: (priority[x["race_type"]], -x["wanted"]))[0]
        c["wanted"] -= 1

    return data


def simulate_round(round_df, profile):
    data = []

    for race_id, race in round_df.groupby("race_id"):
        f = flags(race)
        rt = race_type(f)

        wanted = profile["counts"][rt]

        # Om loppet skulle vara spik/1 streck men träffar no-spik-regeln:
        # höj till minst 2 streck.
        if profile["no_spik_flag"] and f[profile["no_spik_flag"]] and wanted == 1:
            wanted = 2

        data.append({
            "race_id": race_id,
            "race": race.copy(),
            "flags": f,
            "race_type": rt,
            "wanted": wanted,
        })

    data = trim(data)

    details = []

    for d in data:
        race = d["race"].copy()
        f = d["flags"]

        race["pick_score"] = race.apply(lambda r: horse_score(r, f), axis=1)
        ordered = race.sort_values(["pick_score", "total_score"], ascending=False)

        selected = set(f["value_horses"]).intersection(set(race["horse"]))

        for _, row in ordered.iterrows():
            if len(selected) >= d["wanted"]:
                break
            selected.add(row["horse"])

        if len(selected) > d["wanted"]:
            selected = set(
                ordered[ordered["horse"].isin(selected)]
                .head(d["wanted"])["horse"]
                .tolist()
            )

        winner = race[race["won"] == 1].iloc[0]

        details.append({
            "race_id": d["race_id"],
            "race_no": winner["race_no"],
            "race_type": d["race_type"],
            "wanted": len(selected),
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(winner["horse"] in selected),
            "picked": " | ".join(selected),
            "no_spik_65_69": int(f["no_spik_65_69"]),
            "no_spik_65_74": int(f["no_spik_65_74"]),
            "no_spik_under70": int(f["no_spik_under70"]),
            "no_spik_under75": int(f["no_spik_under75"]),
            "top3_sum": round(f["top3_sum"], 1),
        })

    rows = prod([d["wanted"] for d in details])
    hits = sum(d["hit"] for d in details)

    return hits, rows, details


high_dates = payout[payout["payout_8_value"] >= 100000]["date"].drop_duplicates().tolist()

summary_rows = []
round_rows_all = []
details_all = []

for profile in PROFILES:
    profile_rounds = []

    for date in high_dates:
        round_df = df[df["date"] == date].copy()

        if round_df.empty:
            continue

        hits, rows, details = simulate_round(round_df, profile)
        payout_value = round_df["payout_8_value"].iloc[0]

        profile_rounds.append({
            "profile": profile["name"],
            "date": date,
            "payout_8_value": payout_value,
            "rows": rows,
            "hits": hits,
            "eight_right": int(hits >= 8),
            "seven_right": int(hits == 7),
            "six_right": int(hits == 6),
        })

        for d in details:
            d["profile"] = profile["name"]
            d["date"] = date
            d["payout_8_value"] = payout_value
            d["round_hits"] = hits
            d["round_rows"] = rows
            details_all.append(d)

    res = pd.DataFrame(profile_rounds)
    round_rows_all.append(res)

    summary_rows.append({
        "profile": profile["name"],
        "rounds": len(res),
        "avg_rows": round(res["rows"].mean(), 1),
        "max_rows": int(res["rows"].max()),
        "eight_right": int(res["eight_right"].sum()),
        "seven_right": int(res["seven_right"].sum()),
        "six_right": int(res["six_right"].sum()),
        "avg_hits": round(res["hits"].mean(), 3),
        "best_hits": int(res["hits"].max()),
    })

summary = pd.DataFrame(summary_rows).sort_values(
    ["eight_right", "seven_right", "six_right", "avg_hits"],
    ascending=False
)

rounds = pd.concat(round_rows_all, ignore_index=True)
details = pd.DataFrame(details_all)

print()
print("=" * 100)
print("NO SPIK OPEN TOP3SUM SYSTEMTEST MAX 540")
print("=" * 100)
print(summary.to_string(index=False))

print()
print("=" * 100)
print("BÄSTA OMGÅNGAR")
print("=" * 100)
print(
    rounds.sort_values(["hits", "payout_8_value"], ascending=[False, False])
    .head(40)
    .to_string(index=False)
)

summary.to_csv("no_spik_open_top3sum_540_summary.csv", index=False, encoding="utf-8-sig")
rounds.to_csv("no_spik_open_top3sum_540_rounds.csv", index=False, encoding="utf-8-sig")
details.to_csv("no_spik_open_top3sum_540_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("no_spik_open_top3sum_540_summary.csv")
print("no_spik_open_top3sum_540_rounds.csv")
print("no_spik_open_top3sum_540_details.csv")