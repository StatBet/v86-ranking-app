import os
import re

from scripts.parser_v2 import parse_input
from scripts.parser_atg_new import parse_new_atg_format
from scripts.result_parser import parse_results
from scripts.ranking_engine_v3 import add_dynamic_scores, calculate_total_score


HISTORY_FOLDER = r"C:\Users\Grinvald\Desktop\ranking"


def load_text(path):
    with open(path, "r", encoding="latin-1") as f:
        return f.read()


def clean_horse_name(name):
    name = name.replace("\xa0", " ").strip()
    name = re.sub(r"^\d+\s+", "", name)
    return name.lower().strip()


def remove_duplicate_horses(horses):
    seen = set()
    unique = []

    for horse in horses:
        key = clean_horse_name(horse.get("horse", ""))

        if key in seen:
            continue

        seen.add(key)
        unique.append(horse)

    return unique


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


def get_date_from_filename(filename):
    match = re.search(r"(\d{8})", filename)
    return match.group(1) if match else None


start_files = [
    f for f in os.listdir(HISTORY_FOLDER)
    if f.lower().startswith("start") and f.lower().endswith(".txt")
]

total_races = 0
winner_rank_1 = 0
winner_top_3 = 0
winner_top_5 = 0

for start_file in start_files:
    date = get_date_from_filename(start_file)

    if not date:
        continue

    result_file = f"resultat{date}.txt"

    start_path = os.path.join(HISTORY_FOLDER, start_file)
    result_path = os.path.join(HISTORY_FOLDER, result_file)

    if not os.path.exists(result_path):
        print(f"Saknar resultatfil för {start_file}")
        continue

    raw_data = load_text(start_path)
    raw_results = load_text(result_path)

    races = parse_races(raw_data)
    results = parse_results(raw_results)

    print()
    print("=" * 80)
    print(f"OMGÅNG {date}")
    print("=" * 80)
    print("Antal lopp:", len(races))

    for race_data in races:
        race = race_data["race"]
        race_no = str(race["race_no"])

        if race_no not in results:
            continue

        winner = results[race_no]

        horses = remove_duplicate_horses(
            race_data["horses"]
        )

        horses = add_dynamic_scores(
            horses,
            race
        )

        for horse in horses:
            horse["total_score"] = calculate_total_score(horse)

        ranked = sorted(
            horses,
            key=lambda x: x["total_score"],
            reverse=True
        )

        winner_rank = None
        winner_score = None
        top_score = ranked[0]["total_score"] if ranked else 0

        for i, horse in enumerate(ranked, start=1):
            if clean_horse_name(horse["horse"]) == clean_horse_name(winner):
                winner_rank = i
                winner_score = horse["total_score"]
                break

        total_races += 1

        if winner_rank == 1:
            winner_rank_1 += 1

        if winner_rank is not None and winner_rank <= 3:
            winner_top_3 += 1

        if winner_rank is not None and winner_rank <= 5:
            winner_top_5 += 1

        print()
        print(f"Avd {race_no} - {race['track']} {race['distance']}m {race['start']}")
        print(f"Antal hästar: {len(horses)}")
        print(f"Vinnare: {winner}")
        print(f"Rankad: {winner_rank}")
        print(f"Poäng vinnare: {winner_score}")
        print(f"Gap till rank 1: {top_score - winner_score if winner_score is not None else 'N/A'}")
        print("Topp 5:")

        for i, horse in enumerate(ranked[:5], start=1):
            gap = top_score - horse["total_score"]
            print(f"{i}. {horse['horse']} - {horse['total_score']}p - gap {gap}")

print()
print("=" * 80)
print("TOTAL SAMMANFATTNING")
print("=" * 80)

if total_races > 0:
    print(f"Antal lopp analyserade: {total_races}")
    print(f"Vinnare rankad 1: {winner_rank_1}/{total_races} ({round(winner_rank_1 / total_races * 100, 1)}%)")
    print(f"Vinnare topp 3: {winner_top_3}/{total_races} ({round(winner_top_3 / total_races * 100, 1)}%)")
    print(f"Vinnare topp 5: {winner_top_5}/{total_races} ({round(winner_top_5 / total_races * 100, 1)}%)")
else:
    print("Inga lopp analyserade.")