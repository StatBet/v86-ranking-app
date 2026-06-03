import os
import re
import copy
import pandas as pd

from scripts.parser_v2 import parse_input
from scripts.parser_atg_new import parse_new_atg_format
from scripts.result_parser import parse_results

from scripts.ranking_engine_v3 import (
    add_dynamic_scores,
    calculate_total_score
)


HISTORY_FOLDER = r"C:\Users\Grinvald\Desktop\ranking"
OUTPUT_FILE = "ml_dataset.csv"


def load_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


def clean_name(name):
    name = name.replace("\xa0", " ").strip()
    name = re.sub(r"^\d+\s*", "", name)
    return name.lower().strip()


def get_date_from_filename(filename):
    match = re.search(r"(\d{8})", filename)
    return match.group(1) if match else None


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


def remove_duplicate_horses(horses):
    seen = set()
    unique = []

    for horse in horses:
        key = clean_name(horse.get("horse", ""))

        if key in seen:
            continue

        seen.add(key)
        unique.append(horse)

    return unique


def extract_prize_money_raw(raw):
    match = re.search(r"\n([\d\xa0 ]+)\n\d+%", raw)

    if not match:
        return 0

    return int(
        match.group(1)
        .replace("\xa0", "")
        .replace(" ", "")
    )

def extract_start_number_raw(name):
    match = re.match(r"^\s*(\d+)", str(name).replace("\xa0", " "))
    return int(match.group(1)) if match else 0


def extract_post_raw(raw):
    match = re.search(r"\n\d{3,4}\s*:\s*(\d+)\n", raw)
    return int(match.group(1)) if match else 0


def extract_record_raw(raw):
    matches = re.findall(r"\n(\d{1,2},\d[a-zA-Z]*)\n", raw)

    if not matches:
        return ""

    return matches[0]


def time_to_float(value):
    if not value:
        return None

    cleaned = (
        value.lower()
        .replace("a", "")
        .replace("g", "")
        .replace("k", "")
        .replace("m", "")
    )

    try:
        return float(cleaned.replace(",", "."))
    except Exception:
        return None


def extract_avg_time_raw(raw):
    times = re.findall(r"\n(\d{1,2},\d[a-zA-Z]*)\n", raw)

    values = []

    for t in times:
        value = time_to_float(t)

        if value is not None:
            values.append(value)

    if not values:
        return 0

    return round(sum(values) / len(values), 2)


def extract_avg_odds_raw(raw):
    odds = re.findall(r"\n(\d+,\d+)\n\d+'", raw)

    values = []

    for o in odds:
        try:
            values.append(float(o.replace(",", ".")))
        except Exception:
            pass

    if not values:
        return 0

    return round(sum(values) / len(values), 2)


def extract_form_score_raw(raw):
    placements = re.findall(
        r"\n\d{4}-\d{2}-\d{2}\n.*?\n.*?\n([0-9dgk])\n",
        raw,
        re.S
    )

    points = {
        "1": 10,
        "2": 7,
        "3": 5,
        "4": 3,
        "5": 2,
        "0": 0,
        "d": 0,
        "g": 0,
        "k": 0
    }

    score = 0

    for p in placements[:5]:
        score += points.get(p.lower(), 0)

    return score


def extract_latest_start_score_raw(raw):
    placements = re.findall(
        r"\n\d{4}-\d{2}-\d{2}\n.*?\n.*?\n([0-9dgk])\n",
        raw,
        re.S
    )

    if not placements:
        return 0

    points = {
        "1": 10,
        "2": 7,
        "3": 5,
        "4": 3,
        "5": 2,
        "0": 0,
        "d": 0,
        "g": 0,
        "k": 0
    }

    return points.get(placements[0].lower(), 0)


def extract_recent_prize_raw(raw):
    prizes = re.findall(r"\n(\d+)'\n", raw)

    values = []

    for p in prizes[:5]:
        try:
            values.append(int(p) * 1000)
        except Exception:
            pass

    if not values:
        return 0

    high_class = [v for v in values if v >= 100000]

    if len(high_class) < 3:
        return 0

    avg_value = sum(high_class) / len(high_class)

    if avg_value >= 200000:
        return 10

    if avg_value >= 125000:
        return 6

    if avg_value >= 100000:
        return 3

    return 0


def apply_raw_fallbacks(horse):
    raw = horse.get("raw", "")

    horse["prize_money"] = extract_prize_money_raw(raw)
    horse["record"] = extract_record_raw(raw)
    horse["avg_time"] = extract_avg_time_raw(raw)
    horse["avg_odds"] = extract_avg_odds_raw(raw)
    horse["form_score"] = extract_form_score_raw(raw)
    horse["latest_start_score"] = extract_latest_start_score_raw(raw)
    horse["recent_prize_score"] = extract_recent_prize_raw(raw)
    horse["class_change_score"] = horse["recent_prize_score"]
    gallop_count = len(
        re.findall(r"\n(?:d|[0-9]+)?g\n", raw.lower())
    )

    horse["gallop_score"] = -20 if gallop_count >= 2 else 0
    horse["gallop_count"] = gallop_count
    horse["number"] = extract_start_number_raw(horse.get("horse", ""))
    horse["post"] = extract_post_raw(raw)

    return horse


def grouped_speed_scores(horses, key):
    valid = [
        h for h in horses
        if h.get(key, 0) not in [0, None, ""]
    ]

    sorted_h = sorted(
        valid,
        key=lambda x: x.get(key, 0)
    )

    scores = [24, 22, 20, 17, 15, 13, 10, 8]
    result = {}

    current_group = []
    current_start = None
    groups = []

    for h in sorted_h:
        value = h.get(key, 0)

        if not current_group:
            current_group = [h]
            current_start = value
            continue

        if round(value - current_start, 2) <= 0.1:
            current_group.append(h)
        else:
            groups.append(current_group)
            current_group = [h]
            current_start = value

    if current_group:
        groups.append(current_group)

    for i, group in enumerate(groups):
        score = scores[i] if i < len(scores) else 1

        for h in group:
            result[h["horse"]] = score

    return result


rows = []

start_files = [
    f for f in os.listdir(HISTORY_FOLDER)
    if f.lower().startswith("start")
    and f.lower().endswith(".txt")
]

for start_file in start_files:
    date = get_date_from_filename(start_file)

    if not date:
        continue

    result_file = f"resultat{date}.txt"

    start_path = os.path.join(HISTORY_FOLDER, start_file)
    result_path = os.path.join(HISTORY_FOLDER, result_file)

    if not os.path.exists(result_path):
        print("Saknar resultatfil:", result_file)
        continue

    print("Läser:", start_file, "+", result_file)

    raw_start = load_text(start_path)
    raw_result = load_text(result_path)

    races = parse_races(raw_start)
    results = parse_results(raw_result)

    for race_data in races:
        race = race_data["race"]
        race_no = str(race.get("race_no", ""))

        if race_no not in results:
            continue

        winner = results[race_no]

        horses = remove_duplicate_horses(
            copy.deepcopy(race_data["horses"])
        )

        horses = add_dynamic_scores(horses, race)

        for horse in horses:
            apply_raw_fallbacks(horse)

        speed_map = grouped_speed_scores(horses, "avg_time")
        record_map = grouped_speed_scores(horses, "avg_time")

        for horse in horses:
            horse["speed_score"] = speed_map.get(horse["horse"], 0)
            horse["record_score"] = record_map.get(horse["horse"], 0)
            horse["total_score"] = calculate_total_score(horse)

        ranked = sorted(
            horses,
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )

        top_score = ranked[0].get("total_score", 0) if ranked else 0

        score_rank_map = {}

        for rank, horse in enumerate(ranked, start=1):
            score_rank_map[clean_name(horse.get("horse", ""))] = rank

        for horse in horses:
            horse_name = horse.get("horse", "")
            is_winner = clean_name(horse_name) == clean_name(winner)
            model_rank = score_rank_map.get(clean_name(horse_name), 999)

            rows.append({
                "date": date,
                "race_id": f"{date}_{race_no}",
                "race_no": race_no,
                "track": race.get("track", ""),
                "distance": race.get("distance", 0),
                "start_type": race.get("start", ""),
                "field_size": len(horses),
                "horse": horse_name,
                "winner": winner,
                "won": 1 if is_winner else 0,
                "model_rank": model_rank,
                "is_model_rank_1": 1 if model_rank == 1 else 0,
                "score_gap_to_top": top_score - horse.get("total_score", 0),

                "total_score": horse.get("total_score", 0),
                "speed_score": horse.get("speed_score", 0),
                "record_score": horse.get("record_score", 0),
                "form_score": horse.get("form_score", 0),
                "stallform_score": horse.get("stallform_score", 0),
                "latest_start_score": horse.get("latest_start_score", 0),
                "post_score": horse.get("post_score", 0),
                "driver_score": horse.get("driver_score", 0),
                "driver_change_score": horse.get("driver_change_score", 0),
                "starts_score": horse.get("starts_score", 0),
                "win_score": horse.get("win_score", 0),
                "place_score": horse.get("place_score", 0),
                "spel_score": horse.get("spel_score", 0),
                "prize_money_score": horse.get("prize_money_score", 0),
                "recent_prize_score": horse.get("recent_prize_score", 0),
                "class_change_score": horse.get("class_change_score", 0),
                "avg_odds_score": horse.get("avg_odds_score", 0),
                "wagon_score": horse.get("wagon_score", 0),
                "shoe_score": horse.get("shoe_score", 0),
                "inactivity_score": horse.get("inactivity_score", 0),
                "distance_addition_score": horse.get("distance_addition_score", 0),
                "gender_score": horse.get("gender_score", 0),
                "gallop_score": horse.get("gallop_score", 0),

                "avg_time": horse.get("avg_time", 0),
                "avg_odds": horse.get("avg_odds", 0),
                "starts": horse.get("starts", 0),
                "wins": horse.get("wins", 0),
                "seconds": horse.get("seconds", 0),
                "thirds": horse.get("thirds", 0),
                "win_percent": horse.get("win_percent", 0),
                "place_percent": horse.get("place_percent", 0),
                "percent": horse.get("percent", 0),
                "prize_money": horse.get("prize_money", 0),
                "post": horse.get("post", 0),
                "number": horse.get("number", 0),
                "raw": horse.get("raw", "")
            })


df = pd.DataFrame(rows)

print()
print("=" * 80)
print("ML DATASET KLART")
print("=" * 80)
print("Rader:", len(df))
print("Lopp:", df["race_id"].nunique() if not df.empty else 0)
print("Vinnare:", int(df["won"].sum()) if not df.empty else 0)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print()
print("Sparad som:")
print(OUTPUT_FILE)