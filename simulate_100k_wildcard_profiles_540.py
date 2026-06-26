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
    spread = r1 - scores.get(8, 0)
    gap13 = r1 - scores.get(3, 0)
    gap14 = r1 - scores.get(4, 0)
    return spread < 70 and gap13 < 30 and gap14 < 30


def get_flags(race):
    winner = race[race["won"] == 1].iloc[0]

    r1 = race[race["model_rank"] == 1]
    r2 = race[race["model_rank"] == 2]

    score_gap = 999
    spike_gap = 999
    rank1_spike = 0

    if len(r1):
        rank1_spike = float(r1.iloc[0]["spike_score"])

    if len(r1) and len(r2):
        score_gap = float(r1.iloc[0]["total_score"] - r2.iloc[0]["total_score"])
        spike_gap = float(r1.iloc[0]["spike_score"] - r2.iloc[0]["spike_score"])

    spread = float(winner["spread"])
    open_lopp = is_open_lopp(race)
    top3_sum = float(race.nlargest(3, "percent")["percent"].sum())
    total_sum = float(race["total_score"].sum())
    spike_sum = float(race["spike_score"].sum())

    value = race[
        race["model_rank"].between(4, 7)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 105)
    ]

    plus = race[
        race["model_rank"].between(3, 5)
        & race["total_score"].between(125, 134)
        & (race["spike_score"] >= 150)
    ]

    has_value = len(value) > 0

    return {
        "spread": spread,
        "open": open_lopp,
        "top3_sum": top3_sum,
        "top3_warning": total_sum >= 1538,
        "compact": total_sum <= 1165 or spike_sum <= 1097,

        "has_value": has_value,
        "value_horses": set(value["horse"].tolist()),
        "plus_horses": set(plus["horse"].tolist()),

        "level1": has_value and spread < 70,
        "level2": open_lopp and has_value,
        "level3": open_lopp and has_value and 65 <= top3_sum < 75,

        "trap_a": has_value and score_gap < 10,
        "trap_b": has_value and spike_gap < 25,
        "trap_c": has_value and rank1_spike < 175,
        "trap_any": has_value and (
            score_gap < 10
            or spike_gap < 25
            or rank1_spike < 175
        ),

        "score_gap": score_gap,
        "spike_gap": spike_gap,
        "rank1_spike": rank1_spike,
    }


def race_type(flags):
    if flags["level3"]:
        return "level3"
    if flags["level2"]:
        return "level2"
    if flags["level1"]:
        return "level1"
    if flags["top3_warning"]:
        return "top3"
    if flags["open"]:
        return "open"
    if flags["compact"]:
        return "compact"
    return "normal"


def wildcard_score(flags):
    score = 0

    if flags["level3"]:
        score += 100
    if flags["level2"]:
        score += 70
    if flags["level1"]:
        score += 40
    if flags["top3_warning"]:
        score += 45
    if flags["trap_any"]:
        score += 35
    if 65 <= flags["top3_sum"] < 75:
        score += 20
    if flags["top3_sum"] < 65:
        score += 10

    return score


def base_score(row, flags):
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

    if horse in flags["value_horses"]:
        p += 90
    if horse in flags["plus_horses"]:
        p += 45

    if flags["level2"] and 5 <= rank <= 9:
        p += 30

    if flags["top3_warning"] and 5 <= rank <= 10:
        p += 18

    if flags["trap_any"] and rank == 1:
        p -= 35

    if pct <= 10:
        p += 10
    if spike >= 150:
        p += 10
    if score >= 120:
        p += 5

    return p


def wildcard_score_horse(row, flags, style):
    rank = int(row["model_rank"])
    horse = row["horse"]
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])

    p = 0

    if style == "longs_6_11":
        if 6 <= rank <= 11:
            p += 200 - abs(rank - 8) * 8
        if rank <= 5:
            p -= 80

    elif style == "barbell":
        if rank in [1, 2, 3]:
            p += 80
        if 6 <= rank <= 11:
            p += 95 - abs(rank - 8) * 7
        if rank in [4, 5]:
            p -= 35

    elif style == "no_rank1_2_8":
        if 2 <= rank <= 8:
            p += 160 - rank * 7
        if rank == 1:
            p -= 100
        if 9 <= rank <= 11:
            p += 30

    if horse in flags["value_horses"]:
        p += 90
    if horse in flags["plus_horses"]:
        p += 35

    if pct <= 10:
        p += 22
    if pct <= 5:
        p += 10
    if spike >= 120:
        p += 8
    if score >= 120:
        p += 8

    return p


PROFILES = [
    {
        "name": "W1_one_wildcard_longs",
        "wildcards": 1,
        "wildcard_style": "longs_6_11",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "W2_two_wildcards_longs",
        "wildcards": 2,
        "wildcard_style": "longs_6_11",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "W3_two_wildcards_barbell",
        "wildcards": 2,
        "wildcard_style": "barbell",
        "counts": {"level3": 7, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "W4_two_wildcards_no_rank1",
        "wildcards": 2,
        "wildcard_style": "no_rank1_2_8",
        "counts": {"level3": 7, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
    {
        "name": "W5_three_wildcards_lite",
        "wildcards": 3,
        "wildcard_style": "barbell",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
    },
]


def trim_to_budget(races_data):
    priority = {
        "normal": 1,
        "compact": 2,
        "open": 3,
        "level1": 4,
        "top3": 5,
        "level2": 6,
        "level3": 7,
    }

    while prod([x["wanted"] for x in races_data]) > MAX_ROWS:
        candidates = [x for x in races_data if x["wanted"] > 1]
        if not candidates:
            break

        c = sorted(
            candidates,
            key=lambda x: (priority.get(x["race_type"], 9), -x["wanted"])
        )[0]

        c["wanted"] -= 1

    return races_data


def select_horses(race, flags, wanted, is_wildcard, style):
    race = race.copy()

    selected = set()

    if flags["value_horses"]:
        for h in flags["value_horses"]:
            selected.add(h)

    if is_wildcard:
        race["pick_score"] = race.apply(
            lambda r: wildcard_score_horse(r, flags, style),
            axis=1
        )
    else:
        race["pick_score"] = race.apply(
            lambda r: base_score(r, flags),
            axis=1
        )

    ordered = race.sort_values(["pick_score", "total_score"], ascending=False)

    for _, row in ordered.iterrows():
        if len(selected) >= wanted:
            break
        selected.add(row["horse"])

    final = ordered[ordered["horse"].isin(selected)].copy()

    if len(final) > wanted:
        final = final.sort_values(["pick_score", "total_score"], ascending=False).head(wanted)

    return final["horse"].tolist()


def simulate_round(round_df, profile):
    races_data = []

    for race_id, race in round_df.groupby("race_id"):
        race = race.copy()
        flags = get_flags(race)
        rt = race_type(flags)

        races_data.append({
            "race_id": race_id,
            "race": race,
            "flags": flags,
            "race_type": rt,
            "wanted": profile["counts"][rt],
            "wildcard_score": wildcard_score(flags),
        })

    wildcard_ids = set(
        x["race_id"]
        for x in sorted(races_data, key=lambda r: r["wildcard_score"], reverse=True)
        if x["wildcard_score"] > 0
    [:profile["wildcards"]]
    )

    for r in races_data:
        if r["race_id"] in wildcard_ids:
            r["wanted"] = max(r["wanted"], 6)

    races_data = trim_to_budget(races_data)

    details = []

    for rd in sorted(races_data, key=lambda x: x["race"].iloc[0]["race_no"]):
        race = rd["race"]
        winner = race[race["won"] == 1].iloc[0]
        is_wc = rd["race_id"] in wildcard_ids

        picked = select_horses(
            race,
            rd["flags"],
            rd["wanted"],
            is_wc,
            profile["wildcard_style"]
        )

        details.append({
            "race_id": rd["race_id"],
            "race_no": winner["race_no"],
            "race_type": rd["race_type"],
            "wanted": len(picked),
            "wildcard": int(is_wc),
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(winner["horse"] in picked),
            "picked": " | ".join(picked),
            "level1": int(rd["flags"]["level1"]),
            "level2": int(rd["flags"]["level2"]),
            "level3": int(rd["flags"]["level3"]),
            "trap_any": int(rd["flags"]["trap_any"]),
            "top3_sum": round(rd["flags"]["top3_sum"], 1),
            "wildcard_score": rd["wildcard_score"],
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
print("100K WILDCARD PROFILES MAX 540")
print("=" * 100)
print(summary.to_string(index=False))

print()
print("=" * 100)
print("BÄSTA OMGÅNGAR")
print("=" * 100)
print(
    rounds.sort_values(["hits", "payout_8_value"], ascending=[False, False])
    .head(60)
    .to_string(index=False)
)

summary.to_csv("100k_wildcard_profiles_540_summary.csv", index=False, encoding="utf-8-sig")
rounds.to_csv("100k_wildcard_profiles_540_rounds.csv", index=False, encoding="utf-8-sig")
details.to_csv("100k_wildcard_profiles_540_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("100k_wildcard_profiles_540_summary.csv")
print("100k_wildcard_profiles_540_rounds.csv")
print("100k_wildcard_profiles_540_details.csv")