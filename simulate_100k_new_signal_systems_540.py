import pandas as pd
from math import prod

MAX_ROWS = 540
MIN_ROWS_TARGET = 360

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


def get_score_gap_1_2(race):
    r1 = race[race["model_rank"] == 1]
    r2 = race[race["model_rank"] == 2]

    if len(r1) == 0 or len(r2) == 0:
        return 999

    return float(r1.iloc[0]["total_score"] - r2.iloc[0]["total_score"])


def get_real_spike_candidate(race):
    ranked = race.sort_values("total_score", ascending=False).reset_index(drop=True)

    if len(ranked) == 0:
        return None

    best = ranked.iloc[0]

    if len(ranked) > 1:
        r1 = ranked.iloc[0]
        r2 = ranked.iloc[1]
        score_gap = r1["total_score"] - r2["total_score"]

        if r1["post"] >= 6 and r2["post"] <= 8 and score_gap < 10:
            best = r2

    return best["horse"]


def race_flags(race):
    winner = race[race["won"] == 1].iloc[0]

    spread = winner["spread"]
    open_lopp = is_open_lopp(race)
    top3_sum = race.nlargest(3, "percent")["percent"].sum()
    total_sum = race["total_score"].sum()
    score_gap_1_2 = get_score_gap_1_2(race)

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
        "open_lopp": open_lopp,
        "top3_sum": top3_sum,
        "top3_warning": total_sum >= 1538,
        "has_value": has_value,
        "has_plus": len(plus) > 0,
        "level1_valuehunt": has_value and spread < 70,
        "level2_scrallrisk": open_lopp and has_value,
        "level3_extreme": open_lopp and has_value and 65 <= top3_sum < 75,
        "spik_yellow": has_value,
        "spik_red": has_value and score_gap_1_2 < 10,
        "score_gap_1_2": score_gap_1_2,
        "value_horses": set(value["horse"].tolist()),
        "plus_horses": set(plus["horse"].tolist()),
    }


def horse_priority(row, flags):
    rank = int(row["model_rank"])
    pct = float(row["percent"])
    score = float(row["total_score"])
    spike = float(row["spike_score"])

    points = 200 - rank * 12

    if rank == 1:
        points += 90
    if rank == 2:
        points += 55
    if rank == 3:
        points += 35

    if row["horse"] in flags["value_horses"]:
        points += 90
    if row["horse"] in flags["plus_horses"]:
        points += 45

    if flags["open_lopp"] and 5 <= rank <= 8 and score >= 120 and pct <= 15:
        points += 35

    if flags["top3_warning"] and 4 <= rank <= 9:
        points += 18

    if pct <= 10:
        points += 10
    if pct <= 5:
        points += 6

    if spike >= 150:
        points += 12
    elif spike >= 120:
        points += 6

    return points


def select_horses(race, flags, wanted_count, force_spike_horse=None):
    race = race.copy()

    selected = set()

    if force_spike_horse:
        selected.add(force_spike_horse)
    else:
        for r in [1, 2]:
            h = race[race["model_rank"] == r]
            if len(h):
                selected.add(h.iloc[0]["horse"])

    for h in flags["value_horses"]:
        selected.add(h)

    if flags["level2_scrallrisk"] or flags["level3_extreme"]:
        scrall = race[
            race["model_rank"].between(5, 8)
            & (race["total_score"] >= 120)
            & (race["percent"] <= 15)
        ]
        for h in scrall["horse"].tolist():
            selected.add(h)

    race["priority"] = race.apply(lambda r: horse_priority(r, flags), axis=1)
    ordered = race.sort_values(["priority", "total_score"], ascending=False)

    for _, row in ordered.iterrows():
        if len(selected) >= wanted_count:
            break
        selected.add(row["horse"])

    final = ordered[ordered["horse"].isin(selected)].copy()

    if len(final) > wanted_count:
        final = final.sort_values(["priority", "total_score"], ascending=False).head(wanted_count)

    return final["horse"].tolist()


PROFILES = [
    {
        "name": "balanced_540",
        "max_spikes": 2,
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
        "name": "valuehunt_540",
        "max_spikes": 1,
        "counts": {
            "level3": 7,
            "level2": 6,
            "level1": 5,
            "top3": 6,
            "open": 5,
            "compact": 2,
            "normal": 3,
        },
    },
    {
        "name": "scrallrisk_540",
        "max_spikes": 1,
        "counts": {
            "level3": 7,
            "level2": 6,
            "level1": 4,
            "top3": 6,
            "open": 5,
            "compact": 2,
            "normal": 3,
        },
    },
    {
        "name": "safer_540",
        "max_spikes": 2,
        "counts": {
            "level3": 5,
            "level2": 5,
            "level1": 4,
            "top3": 5,
            "open": 4,
            "compact": 2,
            "normal": 3,
        },
    },
]


def race_type(flags):
    if flags["level3_extreme"]:
        return "level3"
    if flags["level2_scrallrisk"]:
        return "level2"
    if flags["level1_valuehunt"]:
        return "level1"
    if flags["top3_warning"]:
        return "top3"
    if flags["open_lopp"]:
        return "open"
    if flags["spread"] >= 80:
        return "compact"
    return "normal"


def build_round_system(round_df, profile):
    races_data = []

    for race_id, race in round_df.groupby("race_id"):
        race = race.copy()
        flags = race_flags(race)
        rt = race_type(flags)
        spike_candidate = get_real_spike_candidate(race)

        spike_row = race[race["horse"] == spike_candidate].iloc[0]
        safe_spike = (
            not flags["spik_red"]
            and not flags["level2_scrallrisk"]
            and not flags["level3_extreme"]
            and not flags["top3_warning"]
            and spike_row["model_rank"] <= 2
            and spike_row["spike_score"] >= 250
        )

        races_data.append({
            "race_id": race_id,
            "race": race,
            "flags": flags,
            "race_type": rt,
            "spike_candidate": spike_candidate,
            "safe_spike": safe_spike,
            "wanted": profile["counts"][rt],
        })

    # välj max X säkra spikar med högst spike_score
    safe_spikes = []
    for rd in races_data:
        if rd["safe_spike"]:
            row = rd["race"][rd["race"]["horse"] == rd["spike_candidate"]].iloc[0]
            safe_spikes.append((row["spike_score"], rd["race_id"]))

    safe_spike_ids = set(
        race_id for _, race_id in sorted(safe_spikes, reverse=True)[:profile["max_spikes"]]
    )

    for rd in races_data:
        if rd["race_id"] in safe_spike_ids:
            rd["wanted"] = 1

    def current_rows():
        return prod([max(1, rd["wanted"]) for rd in races_data])

    # trimma om systemet blir för stort
    while current_rows() > MAX_ROWS:
        candidates = [
            rd for rd in races_data
            if rd["wanted"] > 1
        ]

        if not candidates:
            break

        def trim_priority(rd):
            order = {
                "normal": 1,
                "compact": 2,
                "open": 3,
                "top3": 4,
                "level1": 5,
                "level2": 6,
                "level3": 7,
            }
            return order.get(rd["race_type"], 9), rd["wanted"]

        rd = sorted(candidates, key=trim_priority)[0]
        rd["wanted"] -= 1

    # fyll på där det ger mest nytta, om plats finns
    while current_rows() < MIN_ROWS_TARGET:
        candidates = [
            rd for rd in races_data
            if rd["wanted"] < len(rd["race"])
            and rd["race_type"] in ["level3", "level2", "level1", "top3", "open"]
        ]

        if not candidates:
            break

        def expand_priority(rd):
            order = {
                "level3": 1,
                "level2": 2,
                "level1": 3,
                "top3": 4,
                "open": 5,
            }
            return order.get(rd["race_type"], 9), rd["wanted"]

        rd = sorted(candidates, key=expand_priority)[0]
        old = rd["wanted"]
        rd["wanted"] += 1

        if current_rows() > MAX_ROWS:
            rd["wanted"] = old
            break

    selections = []
    detail_rows = []

    for rd in sorted(races_data, key=lambda x: x["race"].iloc[0]["race_no"]):
        force = rd["spike_candidate"] if rd["race_id"] in safe_spike_ids else None
        picked = select_horses(rd["race"], rd["flags"], rd["wanted"], force)

        winner = rd["race"][rd["race"]["won"] == 1].iloc[0]
        hit = winner["horse"] in picked

        selections.append(set(picked))

        detail_rows.append({
            "race_id": rd["race_id"],
            "race_no": winner["race_no"],
            "race_type": rd["race_type"],
            "wanted": len(picked),
            "rows_factor": len(picked),
            "safe_spike": int(rd["race_id"] in safe_spike_ids),
            "spike_candidate": rd["spike_candidate"],
            "winner": winner["horse"],
            "winner_rank": int(winner["model_rank"]),
            "winner_percent": winner["percent"],
            "hit": int(hit),
            "picked": " | ".join(picked),
            "level1": int(rd["flags"]["level1_valuehunt"]),
            "level2": int(rd["flags"]["level2_scrallrisk"]),
            "level3": int(rd["flags"]["level3_extreme"]),
            "spik_red": int(rd["flags"]["spik_red"]),
            "top3_sum": round(rd["flags"]["top3_sum"], 1),
        })

    hits = sum(1 for rd in detail_rows if rd["hit"] == 1)
    rows_count = prod([len(s) for s in selections])

    return hits, rows_count, detail_rows


summary_rows = []
all_details = []

high_payout_dates = (
    payout[payout["payout_8_value"] >= 100000]["date"]
    .drop_duplicates()
    .tolist()
)

for profile in PROFILES:
    profile_results = []

    for date in high_payout_dates:
        round_df = df[df["date"] == date].copy()

        if round_df.empty:
            continue

        hits, rows_count, detail_rows = build_round_system(round_df, profile)

        payout_value = round_df["payout_8_value"].iloc[0]

        profile_results.append({
            "profile": profile["name"],
            "date": date,
            "payout_8_value": payout_value,
            "rows": rows_count,
            "hits": hits,
            "eight_right": int(hits >= 8),
            "seven_right": int(hits == 7),
            "six_right": int(hits == 6),
        })

        for d in detail_rows:
            d["profile"] = profile["name"]
            d["date"] = date
            d["payout_8_value"] = payout_value
            d["round_hits"] = hits
            d["round_rows"] = rows_count
            all_details.append(d)

    res = pd.DataFrame(profile_results)

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
        f"100k_system_results_{profile['name']}.csv",
        index=False,
        encoding="utf-8-sig"
    )

summary = pd.DataFrame(summary_rows).sort_values(
    ["eight_right", "seven_right", "avg_hits"],
    ascending=False
)

details = pd.DataFrame(all_details)

print()
print("=" * 100)
print("100K+ SYSTEMSIMULERING - NYA SIGNALER MAX 540")
print("=" * 100)
print(summary.to_string(index=False))

summary.to_csv(
    "100k_new_signal_systems_540_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

details.to_csv(
    "100k_new_signal_systems_540_details.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("Sparat:")
print("100k_new_signal_systems_540_summary.csv")
print("100k_new_signal_systems_540_details.csv")
print("100k_system_results_*.csv")