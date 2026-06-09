import os
import re
import copy

from scripts.parser_v2 import parse_input
from scripts.parser_atg_new import parse_new_atg_format
from scripts.result_parser import parse_results

from scripts.ranking_engine_v3 import (
    add_dynamic_scores,
    calculate_total_score
)

HISTORY_FOLDER = r"C:\Users\Grinvald\Desktop\ranking"


def load_text(path):
    with open(path, "r", encoding="latin-1") as f:
        return f.read()


def clean_name(name):
    name = re.sub(r"^\d+\s*", "", name)
    return name.lower().strip()


def parse_races(raw_data):
    races = parse_input(raw_data)

    races = [
        r for r in races
        if r["race"].get("track") != "UNKNOWN"
        and r["race"].get("distance", 0) > 0
        and r["race"].get("start") != "unknown"
    ]

    if not races or any(len(r["horses"]) <= 1 for r in races):
        races = parse_new_atg_format(raw_data)

    return races


def get_date(filename):
    match = re.search(r"(\d{8})", filename)
    return match.group(1) if match else None


def get_speed_rank(horse, ranked):
    sorted_by_speed = sorted(
        ranked,
        key=lambda x: x.get("speed_score", 0),
        reverse=True
    )

    for i, h in enumerate(sorted_by_speed, start=1):
        if clean_name(h["horse"]) == clean_name(horse["horse"]):
            return i

    return 999


def calculate_spike_score(first, second, ranked):
    gap = first["total_score"] - second["total_score"]
    

    spike_score = 0

    spike_score += gap * 2
    spike_score += first.get("total_score", 0) * 0.25
    spike_score += first.get("driver_score", 0) * 0.5
    spike_score += first.get("place_score", 0) * 0.3
    spike_score += first.get("win_score", 0) * 0.5

    spike_score += first.get("form_score", 0) * 2.0
    spike_score += first.get("latest_start_score", 0) * 2.5

    

    if first.get("gallop_score", 0) < 0:
        spike_score -= 12

    if first.get("inactivity_score", 0) < 0:
        spike_score -= 5

    return round(spike_score, 2)


dataset = []

start_files = [
    f for f in os.listdir(HISTORY_FOLDER)
    if f.startswith("start")
]

for start_file in start_files:
    date = get_date(start_file)

    if not date:
        continue

    result_file = f"resultat{date}.txt"

    start_path = os.path.join(HISTORY_FOLDER, start_file)
    result_path = os.path.join(HISTORY_FOLDER, result_file)

    if not os.path.exists(result_path):
        continue

    raw_start = load_text(start_path)
    raw_result = load_text(result_path)

    races = parse_races(raw_start)
    results = parse_results(raw_result)

    for race_data in races:
        race_no = str(race_data["race"]["race_no"])

        if race_no not in results:
            continue

        dataset.append({
            "date": date,
            "race_no": race_no,
            "race": race_data["race"],
            "horses": copy.deepcopy(race_data["horses"]),
            "winner": results[race_no]
        })


candidates = []

for item in dataset:
    race = item["race"]
    horses = add_dynamic_scores(
        copy.deepcopy(item["horses"]),
        race
    )
    
 
    for horse in horses:
        horse["total_score"] = calculate_total_score(horse)

    ranked = sorted(
        horses,
        key=lambda x: x["total_score"],
        reverse=True
    )

    if len(ranked) < 2:
        continue

    first = ranked[0]
    second = ranked[1]

    spike_score = calculate_spike_score(
        first,
        second,
        ranked
    )

    gap = first["total_score"] - second["total_score"]

    did_win = clean_name(first["horse"]) == clean_name(item["winner"])

    candidates.append({
        "date": item["date"],
        "race_no": item["race_no"],
        "horse": first["horse"],
        "winner": item["winner"],
        "won": did_win,
        "spike_score": spike_score,
        "total_score": first["total_score"],
        "gap": gap,
        "driver_score": first.get("driver_score", 0),
        "speed_score": first.get("speed_score", 0),
        "place_score": first.get("place_score", 0),
        "win_score": first.get("win_score", 0),
        "gallop_score": first.get("gallop_score", 0)
    })


candidates = sorted(
    candidates,
    key=lambda x: x["spike_score"],
    reverse=True
)


print("=" * 80)
print("SPIKMODELL - TOPP KANDIDATER")
print("=" * 80)
print(f"Antal lopp analyserade: {len(dataset)}")
print(f"Antal spikkandidater: {len(candidates)}")

for limit in [20, 30, 40, 50, 60, 70, 80]:
    selected = candidates[:limit]

    if not selected:
        continue

    wins = sum(1 for c in selected if c["won"])
    pct = round(wins / len(selected) * 100, 1)

    print()
    print(
        f"Topp {limit} spikar | "
        f"Rätt: {wins}/{len(selected)} | "
        f"Träff%: {pct}"
    )


print()
print("=" * 80)
print("TOPP 40 DETALJER")
print("=" * 80)

for i, c in enumerate(candidates[:40], start=1):
    result = "RÄTT" if c["won"] else "FEL"

    print(
        f"{i}. {c['date']} Avd {c['race_no']} | "
        f"{c['horse']} | {result} | "
        f"Vinnare: {c['winner']} | "
        f"SpikScore: {c['spike_score']} | "
        f"Tot: {c['total_score']} | "
        f"Gap: {c['gap']} | "
        f"Kusk: {c['driver_score']} | "
        f"Speed: {c['speed_score']} | "
        f"Plats: {c['place_score']} | "
        f"Galopp: {c['gallop_score']}"
    )