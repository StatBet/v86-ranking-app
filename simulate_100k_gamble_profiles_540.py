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
    r1 = race[race["model_rank"] == 1]
    r2 = race[race["model_rank"] == 2]
    winner = race[race["won"] == 1].iloc[0]

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


def pick_score(row, flags, profile):
    rank = int(row["model_rank"])
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])
    horse = row["horse"]

    p = 200 - rank * 10

    if rank == 1:
        p += 75
    elif rank == 2:
        p += 55
    elif rank == 3:
        p += 35
    elif rank <= 5:
        p += 18

    if horse in flags["value_horses"]:
        p += 85

    if horse in flags["plus_horses"]:
        p += 40

    if flags["level1"] and 4 <= rank <= 7:
        p += 25

    if flags["level2"] and 5 <= rank <= 9:
        p += 35

    if flags["level3"]:
        if 6 <= rank <= 11:
            p += profile["level3_long_bonus"]
        if rank <= 5:
            p += profile["level3_top_bonus"]
        if pct <= 12:
            p += 18

    if flags["trap_any"]:
        if rank == 1:
            p -= profile["trap_rank1_penalty"]
        if 2 <= rank <= 8:
            p += 22

    if flags["top3_warning"] and 5 <= rank <= 10:
        p += 20

    if profile["barbell"]:
        if flags["level3"]:
            if rank in [1, 2, 3, 7, 8, 9, 10, 11]:
                p += 30
            if rank in [4, 5, 6]:
                p -= 15

    if spike >= 150:
        p += 10
    elif spike >= 120:
        p += 5

    if score >= 130:
        p += 8
    elif score >= 120:
        p += 4

    return p


PROFILES = [
    {
        "name": "P1_balanced_no_spiktrap_remove",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
        "trap_rank1_penalty": 35,
        "remove_rank1_level3": False,
        "remove_rank1_trap": False,
        "force_level3_longs": 2,
        "level3_long_bonus": 55,
        "level3_top_bonus": 25,
        "barbell": False,
    },
    {
        "name": "P2_level3_skip_rank1",
        "counts": {"level3": 7, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
        "trap_rank1_penalty": 45,
        "remove_rank1_level3": True,
        "remove_rank1_trap": False,
        "force_level3_longs": 4,
        "level3_long_bonus": 75,
        "level3_top_bonus": 5,
        "barbell": False,
    },
    {
        "name": "P3_level3_rank6_11",
        "counts": {"level3": 6, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
        "trap_rank1_penalty": 70,
        "remove_rank1_level3": True,
        "remove_rank1_trap": False,
        "force_level3_longs": 6,
        "level3_long_bonus": 95,
        "level3_top_bonus": -20,
        "barbell": False,
    },
    {
        "name": "P4_barbell_level3",
        "counts": {"level3": 7, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
        "trap_rank1_penalty": 50,
        "remove_rank1_level3": False,
        "remove_rank1_trap": False,
        "force_level3_longs": 4,
        "level3_long_bonus": 70,
        "level3_top_bonus": 20,
        "barbell": True,
    },
    {
        "name": "P5_trap_skip_rank1",
        "counts": {"level3": 7, "level2": 5, "level1": 4, "top3": 5, "open": 4, "compact": 2, "normal": 3},
        "trap_rank1_penalty": 100,
        "remove_rank1_level3": False,
        "remove_rank1_trap": True,
        "force_level3_longs": 3,
        "level3_long_bonus": 65,
        "level3_top_bonus": 15,
        "barbell": False,
    },
    {
        "name": "P6_ultra_gamble",
        "counts": {"level3": 8, "level2": 6, "level1": 4, "top3": 6, "open": 4, "compact": 1, "normal": 2},
        "trap_rank1_penalty": 120,
        "remove_rank1_level3": True,
        "remove_rank1_trap": True,
        "force_level3_longs": 6,
        "level3_long_bonus": 110,
        "level3_top_bonus": -35,
        "barbell": False,
    },
]


def trim(races_data):
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

        candidate = sorted(
            candidates,
            key=lambda x: (priority.get(x["race_type"], 9), -x["wanted"])
        )[0]

        candidate["wanted"] -= 1

    return races_data


def select(race, flags, profile, wanted):
    race = race.copy()

    eligible = race.copy()

    if profile["remove_rank1_level3"] and flags["level3"]:
        eligible = eligible[eligible["model_rank"] != 1]

    if profile["remove_rank1_trap"] and flags["trap_any"]:
        eligible = eligible[eligible["model_rank"] != 1]

    selected = set()

    for h in flags["value_horses"]:
        if h in set(eligible["horse"]):
            selected.add(h)

    if flags["level3"] and profile["force_level3_longs"] > 0:
        longs = eligible[
            eligible["model_rank"].between(6, 11)
        ].sort_values("model_rank")

        for h in longs["horse"].head(profile["force_level3_longs"]).tolist():
            selected.add(h)

    eligible["pick_score"] = eligible.apply(
        lambda r: pick_score(r, flags, profile),
        axis=1
    )

    ordered = eligible.sort_values(["pick_score", "total_score"], ascending=False)

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
        wanted = profile["counts"][rt]

        races_data.append({
            "race_id": race_id,
            "race": race,
            "flags": flags,
            "race_type": rt,
            "wanted": wanted,
        })

    races_data = trim(races_data)

    details = []

    for rd in sorted(races_data, key=lambda x: x["race"].iloc[0]["race_no"]):
        race = rd["race"]
        flags = rd["flags"]
        winner = race[race["won"] == 1].iloc[0]

        picked = select(race, flags, profile, rd["wanted"])
        hit = winner["horse"] in picked

        details.append({
            "race_id": rd["race_id"],
            "race_no": winner["race_no"],
            "race_type": rd["race_type"],
            "wanted": len(picked),
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(hit),
            "picked": " | ".join(picked),
            "level1": int(flags["level1"]),
            "level2": int(flags["level2"]),
            "level3": int(flags["level3"]),
            "trap_any": int(flags["trap_any"]),
            "trap_a": int(flags["trap_a"]),
            "trap_b": int(flags["trap_b"]),
            "trap_c": int(flags["trap_c"]),
            "top3_sum": round(flags["top3_sum"], 1),
        })

    rows = prod([d["wanted"] for d in details])
    hits = sum(d["hit"] for d in details)

    return hits, rows, details


high_dates = (
    payout[payout["payout_8_value"] >= 100000]["date"]
    .drop_duplicates()
    .tolist()
)

summary_rows = []
round_rows_all = []
detail_rows_all = []

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
            detail_rows_all.append(d)

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
details = pd.DataFrame(detail_rows_all)

print()
print("=" * 100)
print("100K GAMBLE PROFILES MAX 540")
print("=" * 100)
print(summary.to_string(index=False))

print()
print("=" * 100)
print("BÄSTA OMGÅNGAR")
print("=" * 100)
print(
    rounds.sort_values(["hits", "payout_8_value"], ascending=[False, False])
    .head(50)
    .to_string(index=False)
)

summary.to_csv("100k_gamble_profiles_540_summary.csv", index=False, encoding="utf-8-sig")
rounds.to_csv("100k_gamble_profiles_540_rounds.csv", index=False, encoding="utf-8-sig")
details.to_csv("100k_gamble_profiles_540_details.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("100k_gamble_profiles_540_summary.csv")
print("100k_gamble_profiles_540_rounds.csv")
print("100k_gamble_profiles_540_details.csv")