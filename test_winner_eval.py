from scripts.parser_v2 import parse_input
from scripts.parser_atg_new import parse_new_atg_format
from scripts.result_parser import parse_results
from scripts.ranking_engine_v3 import add_dynamic_scores, calculate_total_score


INPUT_FILE = "input/v86_test.txt"


RESULT_TEXT = """
1
2 Chribo Hill
Conrad Lugauer
31

2
3 Mix the Booze
Björn Goop
717

3
6 Orosei Boko
Björn Goop
7603
"""


def load_text(path):
    with open(path, "r", encoding="latin-1") as f:
        return f.read()


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


raw_data = load_text(INPUT_FILE)
races = parse_races(raw_data)
results = parse_results(RESULT_TEXT)

for race_data in races:
    race = race_data["race"]
    race_no = str(race["race_no"])

    if race_no not in results:
        continue

    winner = results[race_no]
    horses = add_dynamic_scores(race_data["horses"], race)

    for horse in horses:
        horse["total_score"] = calculate_total_score(horse)

    ranked = sorted(horses, key=lambda x: x["total_score"], reverse=True)

    winner_rank = None

    for i, horse in enumerate(ranked, start=1):
        if horse["horse"].lower().strip() == winner.lower().strip():
            winner_rank = i
            break

    print()
    print(f"Avd {race_no}")
    print(f"Vinnare: {winner}")
    print(f"Rankad: {winner_rank}")
    print("Topp 5:")

    for i, horse in enumerate(ranked[:5], start=1):
        print(f"{i}. {horse['horse']} ({horse['total_score']})")