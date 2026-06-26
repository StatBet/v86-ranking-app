import pandas as pd
from math import prod

MAX_ROWS = 540
DATASET = "ml_dataset.csv"
PAYOUT_FILE = "payout_vs_winner_percent_rounds.csv"

df = pd.read_csv(DATASET).fillna(0)
payout = pd.read_csv(PAYOUT_FILE)
payout = payout[["date", "payout_8_value"]].drop_duplicates("date")
df = df.merge(payout, on="date", how="left")


def is_open_lopp(race):
    scores = {int(r["model_rank"]): r["total_score"] for _, r in race.iterrows()}
    r1 = scores.get(1, 0)

    spread = r1 - scores.get(8, 0)
    gap13 = r1 - scores.get(3, 0)
    gap14 = r1 - scores.get(4, 0)

    return spread < 70 and gap13 < 30 and gap14 < 30


def get_rank_row(race, rank):
    r = race[race["model_rank"] == rank]
    if len(r):
        return r.iloc[0]
    return None


def get_flags(race):
    r1 = get_rank_row(race, 1)
    r2 = get_rank_row(race, 2)
    winner = race[race["won"] == 1].iloc[0]

    score_gap_1_2 = 999
    spike_gap_1_2 = 999

    if r1 is not None and r2 is not None:
        score_gap_1_2 = r1["total_score"] - r2["total_score"]
        spike_gap_1_2 = r1["spike_score"] - r2["spike_score"]

    spread = winner["spread"]
    open_lopp = is_open_lopp(race)
    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    spike_sum = race["spike_score"].sum()

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

    favorite_trap_a = has_value and score_gap_1_2 < 10
    favorite_trap_b = has_value and spike_gap_1_2 < 25
    favorite_trap_c = has_value and r1 is not None and r1["spike_score"] < 175

    return {
        "spread": spread,
        "open_lopp": open_lopp,
        "top3_sum": top3_sum,
        "top3_warning": total_sum >= 1538,
        "compact": total_sum <= 1165 or spike_sum <= 1097,

        "has_value": has_value,
        "has_plus": len(plus) > 0,
        "value_horses": set(value["horse"].tolist()),
        "plus_horses": set(plus["horse"].tolist()),

        "level1": has_value and spread < 70,
        "level2": open_lopp and has_value,
        "level3": open_lopp and has_value and 65 <= top3_sum < 75,

        "favorite_trap_a": favorite_trap_a,
        "favorite_trap_b": favorite_trap_b,
        "favorite_trap_c": favorite_trap_c,
        "favorite_trap_any": favorite_trap_a or favorite_trap_b or favorite_trap_c,

        "score_gap_1_2": score_gap_1_2,
        "spike_gap_1_2": spike_gap_1_2,
        "rank1_spike": r1["spike_score"] if r1 is not None else 0,
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
    if flags["open_lopp"]:
        return "open"
    if flags["compact"]:
        return "compact"
    return "normal"


def score_horse(row, flags, mode):
    rank = int(row["model_rank"])
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])
    horse = row["horse"]

    points = 200 - rank * 10

    if rank == 1:
        points += 75
    elif rank == 2:
        points += 55
    elif rank == 3:
        points += 38
    elif rank <= 5:
        points += 20

    if horse in flags["value_horses"]:
        points += 90

    if horse in flags["plus_horses"]:
        points += 45

    if flags["level3"]:
        if 6 <= rank <= 11:
            points += 75
        if rank == 1:
            points -= 55
        if pct <= 10:
            points += 25

    elif flags["level2"]:
        if 5 <= rank <= 9:
            points += 45
        if pct <= 15:
            points += 15

    elif flags["level1"]:
        if 4 <= rank <= 7:
            points += 35

    if flags["favorite_trap_any"]:
        if rank == 1:
            points -= 80
        if 2 <= rank <= 8:
            points += 30

    if mode == "aggressive":
        if flags["level3"] and rank == 1:
            points -= 100
        if flags["favorite_trap_any"] and rank == 1:
            points -= 70
        if 7 <= rank <= 11 and pct <= 12:
            points += 28

    if mode == "barbell":
        if flags["level3"]:
            if rank in [1, 2, 3, 6, 7, 8, 9, 10]:
                points += 35
            if rank in [4, 5]:
                points -= 20

    if spike >= 150:
        points += 12
    elif spike >= 120:
        points += 6

    if score >= 130:
        points += 8
    elif score >= 120:
        points += 4

    return points


def base_count(rt, flags, profile):
    counts = profile["counts"].copy()

    wanted = counts.get(rt, 3)

    if flags["favorite_trap_any"]:
        wanted += profile.get("trap_extra", 0)

    if flags["level3"]:
        wanted += profile.get("level3_extra", 0)

    return wanted


def select_horses(race, flags, wanted, profile):
    race = race.copy()
    mode = profile["mode"]

    remove_rank1 = False

    if profile.get("remove_rank1_in_trap", False) and flags["favorite_trap_any"]:
        remove_rank1 = True

    if profile.get("remove_rank1_in_level3", False) and flags["level3"]:
        remove_rank1 = True

    eligible = race.copy()

    if remove_rank1:
        eligible = eligible[eligible["model_rank"] != 1].copy()

    selected = set()

    for h in flags["value_horses"]:
        if h in set(eligible["horse"]):
            selected.add(h)

    if flags["level3"] and profile.get("force_level3_longs", False):
        longshots = eligible[
            eligible["model_rank"].between(6, 11)
        ].sort_values("model_rank")

        for h in longshots["horse"].head(4).tolist():
            selected.add(h)

    eligible["pick_score"] = eligible.apply(
        lambda r: score_horse(r, flags, mode),
        axis=1
    )

    ordered = eligible.sort_values(
        ["pick_score", "total_score"],
        ascending=False
    )

    for _, row in ordered.iterrows():
        if len(selected) >= wanted:
            break
        selected.add(row["horse"])

    final = ordered[ordered["horse"].isin(selected)].copy()

    if len(final) > wanted:
        final = final.sort_values(
            ["pick_score", "total_score"],
            ascending=False
        ).head(wanted)

    return final["horse"].tolist()


PROFILES = [
    {
        "name": "A_control_full",
        "mode": "balanced",
        "remove_rank1_in_trap": False,
        "remove_rank1_in_level3": False,
        "force_level3_longs": False,
        "trap_extra": 0,
        "level3_extra": 0,
        "counts": {
            "level3": 6,
            "level2": 5,
            "level1": 4,
            "top3": 5,
            "open": 4,
            "compact": 2,
            "normal": 3,
        },
    },
    {
        "name": "B_favoritfalla",
        "mode": "balanced",
        "remove_rank1_in_trap": True,
        "remove_rank1_in_level3": False,
        "force_level3_longs": False,
        "trap_extra": 1,
        "level3_extra": 0,
        "counts": {
            "level3": 6,
            "level2": 5,
            "level1": 4,
            "top3": 5,
            "open": 4,
            "compact": 2,
            "normal": 3,
        },
    },
    {
        "name": "C_level3_longs",
        "mode": "aggressive",
        "remove_rank1_in_trap": True,
        "remove_rank1_in_level3": True,
        "force_level3_longs": True,
        "trap_extra": 1,
        "level3_extra": 1,
        "counts": {
            "level3": 7,
            "level2": 5,
            "level1": 4,
            "top3": 5,
            "open": 4,
            "compact": 2,
            "normal": 3,
        },
    },
    {
        "name": "D_barbell",
        "mode": "barbell",
        "remove_rank1_in_trap": True,
        "remove_rank1_in_level3": False,
        "force_level3_longs": True,
        "trap_extra": 1,
        "level3_extra": 1,
        "counts": {
            "level3": 7,
            "level2": 5,
            "level1": 4,
            "top3": 5,
            "open": 4,
            "compact": 2,
            "normal": 3,
        },
    },
]


def current_rows(races_data):
    return prod([max(1, r["wanted"]) for r in races_data])


def trim_to_budget(races_data):
    order = {
        "normal": 1,
        "compact": 2,
        "open": 3,
        "level1": 4,
        "top3": 5,
        "level2": 6,
        "level3": 7,
    }

    while current_rows(races_data) > MAX_ROWS:
        candidates = [r for r in races_data if r["wanted"] > 1]

        if not candidates:
            break

        candidates = sorted(
            candidates,
            key=lambda r: (order.get(r["race_type"], 9), -r["wanted"])
        )

        candidates[0]["wanted"] -= 1

    return races_data


def build_round(round_df, profile):
    races_data = []

    for race_id, race in round_df.groupby("race_id"):
        race = race.copy()
        flags = get_flags(race)
        rt = race_type(flags)

        wanted = base_count(rt, flags, profile)

        races_data.append({
            "race_id": race_id,
            "race": race,
            "flags": flags,
            "race_type": rt,
            "wanted": wanted,
        })

    races_data = trim_to_budget(races_data)

    detail_rows = []

    for rd in sorted(races_data, key=lambda x: x["race"].iloc[0]["race_no"]):
        race = rd["race"]
        winner = race[race["won"] == 1].iloc[0]

        picked = select_horses(
            race,
            rd["flags"],
            rd["wanted"],
            profile
        )

        hit = winner["horse"] in picked

        detail_rows.append({
            "race_id": rd["race_id"],
            "race_no": winner["race_no"],
            "race_type": rd["race_type"],
            "wanted": len(picked),
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(hit),
            "picked": " | ".join(picked),
            "level1": int(rd["flags"]["level1"]),
            "level2": int(rd["flags"]["level2"]),
            "level3": int(rd["flags"]["level3"]),
            "favorite_trap_any": int(rd["flags"]["favorite_trap_any"]),
            "trap_a_gap_under10": int(rd["flags"]["favorite_trap_a"]),
            "trap_b_spikegap_under25": int(rd["flags"]["favorite_trap_b"]),
            "trap_c_rank1spike_under175": int(rd["flags"]["favorite_trap_c"]),
            "score_gap_1_2": rd["flags"]["score_gap_1_2"],
            "spike_gap_1_2": rd["flags"]["spike_gap_1_2"],
            "rank1_spike": rd["flags"]["rank1_spike"],
            "top3_sum": rd["flags"]["top3_sum"],
        })

    hits = sum(d["hit"] for d in detail_rows)
    rows = prod([d["wanted"] for d in detail_rows])

    return hits, rows, detail_rows


summary_rows = []
all_details = []
round_results_all = []

high_dates = (
    payout[payout["payout_8_value"] >= 100000]["date"]
    .drop_duplicates()
    .tolist()
)

for profile in PROFILES:
    round_rows = []

    for date in high_dates:
        round_df = df[df["date"] == date].copy()

        if round_df.empty:
            continue

        hits, rows, details = build_round(round_df, profile)

        payout_value = round_df["payout_8_value"].iloc[0]

        round_rows.append({
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
            all_details.append(d)

    res = pd.DataFrame(round_rows)
    round_results_all.append(res)

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

    res.to_csv(
        f"100k_full_signal_results_{profile['name']}.csv",
        index=False,
        encoding="utf-8-sig"
    )

summary = pd.DataFrame(summary_rows).sort_values(
    ["eight_right", "seven_right", "six_right", "avg_hits"],
    ascending=False
)

details = pd.DataFrame(all_details)
rounds_all = pd.concat(round_results_all, ignore_index=True)

print()
print("=" * 100)
print("100K+ FULL SIGNAL SYSTEMS MAX 540")
print("=" * 100)
print(summary.to_string(index=False))

print()
print("=" * 100)
print("BÄSTA OMGÅNGAR")
print("=" * 100)
print(
    rounds_all.sort_values(
        ["hits", "payout_8_value"],
        ascending=[False, False]
    ).head(40).to_string(index=False)
)

summary.to_csv(
    "100k_full_signal_systems_540_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

details.to_csv(
    "100k_full_signal_systems_540_details.csv",
    index=False,
    encoding="utf-8-sig"
)

rounds_all.to_csv(
    "100k_full_signal_systems_540_rounds.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("Sparat:")
print("100k_full_signal_systems_540_summary.csv")
print("100k_full_signal_systems_540_details.csv")
print("100k_full_signal_systems_540_rounds.csv")
print("100k_full_signal_results_*.csv")