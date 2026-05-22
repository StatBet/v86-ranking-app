import os
import re
import copy
from itertools import product
from datetime import datetime

from scripts.parser_v2 import parse_input
from scripts.parser_atg_new import parse_new_atg_format
from scripts.result_parser import parse_results
from scripts.ranking_engine_v3 import (
    add_dynamic_scores,
    calculate_total_score,
    scoring_rules
)


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


def apply_inactivity(horses, days_limit, penalty):
    for horse in horses:
        history = horse.get("history", [])

        if not history:
            horse["inactivity_score"] = 0
            continue

        latest_date = history[0].get("date", "")

        try:
            latest_date_obj = datetime.strptime(
                latest_date,
                "%Y-%m-%d"
            )

            days_since = (
                datetime.today() - latest_date_obj
            ).days

            if days_since > days_limit:
                horse["inactivity_score"] = penalty
            else:
                horse["inactivity_score"] = 0

        except:
            horse["inactivity_score"] = 0

    return horses


def load_dataset():
    dataset = []

    start_files = [
        f for f in os.listdir(HISTORY_FOLDER)
        if f.lower().startswith("start") and f.lower().endswith(".txt")
    ]

    for start_file in start_files:
        date = get_date_from_filename(start_file)

        if not date:
            continue

        result_file = f"resultat{date}.txt"

        start_path = os.path.join(HISTORY_FOLDER, start_file)
        result_path = os.path.join(HISTORY_FOLDER, result_file)

        if not os.path.exists(result_path):
            continue

        raw_data = load_text(start_path)
        raw_results = load_text(result_path)

        races = parse_races(raw_data)
        results = parse_results(raw_results)

        for race_data in races:
            race_no = str(race_data["race"]["race_no"])

            if race_no not in results:
                continue

            dataset.append({
                "date": date,
                "race": race_data["race"],
                "horses": remove_duplicate_horses(race_data["horses"]),
                "winner": results[race_no]
            })

    return dataset


def evaluate_dataset(
    dataset,
    use_spel=False,
    inactivity_days=60,
    inactivity_penalty=-10
):
    total = 0
    rank_1 = 0
    top_3 = 0
    top_5 = 0
    total_winner_rank = 0
    matched = 0

    for item in dataset:
        race = item["race"]
        winner = item["winner"]
        horses = copy.deepcopy(item["horses"])

        horses = add_dynamic_scores(horses, race)

        horses = apply_inactivity(
            horses,
            inactivity_days,
            inactivity_penalty
        )

        if not use_spel:
            for horse in horses:
                horse["spel_score"] = 0

        for horse in horses:
            horse["total_score"] = calculate_total_score(horse)

        ranked = sorted(
            horses,
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )

        winner_rank = None

        for i, horse in enumerate(ranked, start=1):
            if clean_horse_name(horse["horse"]) == clean_horse_name(winner):
                winner_rank = i
                break

        total += 1

        if winner_rank is not None:
            matched += 1
            total_winner_rank += winner_rank

            if winner_rank == 1:
                rank_1 += 1

            if winner_rank <= 3:
                top_3 += 1

            if winner_rank <= 5:
                top_5 += 1

    avg_rank = round(total_winner_rank / matched, 2) if matched else None

    return {
        "total": total,
        "matched": matched,
        "rank_1": rank_1,
        "top_3": top_3,
        "top_5": top_5,
        "rank_1_pct": round(rank_1 / total * 100, 1) if total else 0,
        "top_3_pct": round(top_3 / total * 100, 1) if total else 0,
        "top_5_pct": round(top_5 / total * 100, 1) if total else 0,
        "avg_rank": avg_rank
    }


def scale_dict_values(points_dict, multiplier):
    for key in points_dict:
        points_dict[key] = int(
            round(points_dict[key] * multiplier)
        )


def add_to_range_points(ranges, amount):
    for row in ranges:
        row["points"] = int(row["points"] + amount)


def set_wagon_bonus(value):
    scoring_rules["american_wagon_bonus"] = value


def set_gallop_penalty(value):
    scoring_rules["gallop_penalty"] = value


def run_optimization():
    original_rules = copy.deepcopy(scoring_rules)
    dataset = load_dataset()

    print("=" * 80)
    print("DATASET")
    print("=" * 80)
    print(f"Antal lopp: {len(dataset)}")

    print()
    print("=" * 80)
    print("NUVARANDE MODELL")
    print("=" * 80)

    baseline = evaluate_dataset(dataset)
    print(baseline)

    best = {
        "score": -999,
        "settings": None,
        "result": None
    }

    form_multipliers = [0.5, 0.75, 1.0, 1.25]
    odds_boosts = [-4, 0, 4, 8]
    use_spel_options = [False, True]
    wagon_bonuses = [0, 5, 10, 15]
    gallop_penalties = [-20, -10, -5, 0]
    inactivity_options = [
        (45, -15),
        (60, -10),
        (75, -8),
        (90, -5),
        (999, 0),
    ]

    combos = list(product(
        form_multipliers,
        odds_boosts,
        use_spel_options,
        wagon_bonuses,
        gallop_penalties,
        inactivity_options
    ))

    print()
    print("=" * 80)
    print(f"TESTAR {len(combos)} KOMBINATIONER")
    print("=" * 80)

    for (
        form_mult,
        odds_boost,
        use_spel,
        wagon_bonus,
        gallop_penalty,
        inactivity_setting
    ) in combos:

        scoring_rules.clear()
        scoring_rules.update(copy.deepcopy(original_rules))

        if "form_points" in scoring_rules:
            scale_dict_values(
                scoring_rules["form_points"],
                form_mult
            )

        if "avg_odds_ranges" in scoring_rules:
            add_to_range_points(
                scoring_rules["avg_odds_ranges"],
                odds_boost
            )

        set_wagon_bonus(wagon_bonus)
        set_gallop_penalty(gallop_penalty)

        inactivity_days, inactivity_penalty = inactivity_setting

        result = evaluate_dataset(
            dataset,
            use_spel=use_spel,
            inactivity_days=inactivity_days,
            inactivity_penalty=inactivity_penalty
        )

        optimization_score = (
    result["top_5"] * 5
    + result["top_3"] * 3
    + result["rank_1"] * 2
    - (result["avg_rank"] or 99) * 0.15
)

        if optimization_score > best["score"]:
            best = {
                "score": optimization_score,
                "settings": {
                    "form_multiplier": form_mult,
                    "odds_boost": odds_boost,
                    "use_spel": use_spel,
                    "wagon_bonus": wagon_bonus,
                    "gallop_penalty": gallop_penalty,
                    "inactivity_days": inactivity_days,
                    "inactivity_penalty": inactivity_penalty
                },
                "result": result
            }

    scoring_rules.clear()
    scoring_rules.update(original_rules)

    print()
    print("=" * 80)
    print("BÄSTA TESTADE INSTÄLLNING")
    print("=" * 80)
    print(best["settings"])
    print(best["result"])


if __name__ == "__main__":
    run_optimization()