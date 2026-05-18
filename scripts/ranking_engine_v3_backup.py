# =========================================================
# RANKING ENGINE V3
# =========================================================

import json
import re

from parser_v2 import parse_input

from speed_feature import (
    calculate_avg_time,
    normalize_distance,
    speed_score_from_avg_times
)

TRACK_POINTS_PATH = "config\\track_points.json"
INPUT_PATH = "input\\input_word_new.txt"


# =========================================================
# LOAD TRACK POINTS
# =========================================================

def load_track_points():
    with open(TRACK_POINTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# DISTANCE GROUP
# =========================================================

def get_track_distance_group(distance):
    if 1609 <= distance <= 1680:
        return "1600"

    if 2100 <= distance <= 2200:
        return "2100"

    return "2600"


# =========================================================
# MANUAL POINTS
# här kan du senare ändra poäng enkelt
# =========================================================

DRIVER_POINTS = {
    "Björn Goop": 10,
    "Magnus A Djuse": 10,
    "Örjan Kihlström": 10,
    "Carl Johan Jepson": 9,
    "Johan Untersteiner": 9,
    "Rikard N Skoglund": 8,
    "Stefan Persson": 8,
    "Conrad Lugauer": 8,
    "Robert Bergh": 8,
    "Victor Rosleff": 7,
}

# Tom tills layouten är färdig.
# Exempel senare:
# SHOE_POINTS = {
#     "Chribo Hill": 5,
#     "Legligin": -3,
# }
SHOE_POINTS = {}


def get_driver_score(driver):
    return DRIVER_POINTS.get(driver, 0)


def get_shoe_score(horse):
    return SHOE_POINTS.get(horse["horse"], 0)


# =========================================================
# POST SCORE
# =========================================================

def get_post_score(post, race, track_points):
    distance_group = get_track_distance_group(
        race["distance"]
    )

    key = f"{distance_group}_{race['start']}"

    points = track_points.get(key)

    if not points:
        return 0

    index = post - 1

    if index < 0:
        return 0

    if index >= len(points):
        return points[-1]

    return points[index]


# =========================================================
# FORM
# =========================================================

FORM_POINTS = {
    "1": 10,
    "2": 7,
    "3": 5,
    "4": 3,
    "5": 2,
    "0": 0,
    "d": 0,
}

TRACK_FORM_POINTS = {
    "Solvalla": 4,
    "Åby": 2,
    "Jägersro": 1,
}

LATEST_START_POINTS = {
    "1": 10,
    "2": 7,
    "3": 5,
}


def split_history_parts(raw):
    return [
        p.strip()
        for p in raw.split("\t")
        if p.strip()
    ]


def get_form_score(history):
    if not history:
        return 0

    score = 0

    for race in history[:5]:
        raw = race.get("raw", "")
        parts = split_history_parts(raw)

        if len(parts) < 3:
            continue

        placement = parts[2].lower()

        score += FORM_POINTS.get(placement, 0)

        track_part = parts[0]

        for track_name, bonus in TRACK_FORM_POINTS.items():
            if track_part.startswith(track_name):
                score += bonus
                break

    return score


def get_latest_start_score(history):
    if not history:
        return 0

    raw = history[0].get("raw", "")
    parts = split_history_parts(raw)

    if len(parts) < 3:
        return 0

    placement = parts[2].lower()

    return LATEST_START_POINTS.get(placement, 0)


# =========================================================
# RECORD SCORE
# =========================================================

def record_to_float(record):
    if not record:
        return None

    try:
        cleaned = record

        for token in [
            "aK", "aM", "aL",
            "a", "K", "M", "L", "g"
        ]:
            cleaned = cleaned.replace(token, "")

        cleaned = cleaned.replace(",", ".")
        cleaned = cleaned.strip()

        return float(cleaned)

    except:
        return None


def get_record_score(record):
    value = record_to_float(record)

    if value is None:
        return 0

    if value <= 10.5:
        return 10
    if value <= 11.0:
        return 9
    if value <= 11.5:
        return 8
    if value <= 12.0:
        return 7
    if value <= 12.5:
        return 6
    if value <= 13.0:
        return 5
    if value <= 13.5:
        return 4
    if value <= 14.0:
        return 3

    return 2


# =========================================================
# STARTS / WINS / PLACE
# =========================================================

def extract_stats_string(raw_text):
    match = re.search(
        r"\b(\d+)-(\d+)-(\d+)\b",
        raw_text
    )

    if not match:
        return None

    first_part = match.group(1)
    seconds = int(match.group(2))
    thirds = int(match.group(3))

    if len(first_part) >= 4:
        starts = int(first_part[:-2])
        wins = int(first_part[-2:])
    else:
        starts = int(first_part[:-1])
        wins = int(first_part[-1])

    return {
        "starts": starts,
        "wins": wins,
        "seconds": seconds,
        "thirds": thirds
    }


def get_starts_score(starts):
    if starts <= 0:
        return 0
    if starts <= 5:
        return -15
    if starts <= 10:
        return -10
    if starts <= 15:
        return -5
    if starts <= 20:
        return 0

    return 10


# =========================================================
# GROUPING
# =========================================================

def grouped_absolute_scores(
    horses,
    value_key,
    points_table,
    threshold
):
    valid = []

    for horse in horses:
        value = horse.get(value_key)

        if value is not None:
            valid.append(horse)

    sorted_horses = sorted(
        valid,
        key=lambda x: x[value_key],
        reverse=True
    )

    groups = []
    current_group = []
    group_start = None

    for horse in sorted_horses:
        value = horse[value_key]

        if not current_group:
            current_group = [horse]
            group_start = value
            continue

        diff = group_start - value

        if diff <= threshold:
            current_group.append(horse)
        else:
            groups.append(current_group)
            current_group = [horse]
            group_start = value

    if current_group:
        groups.append(current_group)

    result = {}

    for i, group in enumerate(groups):
        score = (
            points_table[i]
            if i < len(points_table)
            else 0
        )

        for horse in group:
            result[horse["horse"]] = score

    return result


def grouped_relative_scores(
    horses,
    value_key,
    points_table,
    threshold_percent
):
    valid = []

    for horse in horses:
        value = horse.get(value_key)

        if value and value > 0:
            valid.append(horse)

    sorted_horses = sorted(
        valid,
        key=lambda x: x[value_key],
        reverse=True
    )

    groups = []
    current_group = []
    group_start = None

    for horse in sorted_horses:
        value = horse[value_key]

        if not current_group:
            current_group = [horse]
            group_start = value
            continue

        diff_percent = (
            (group_start - value)
            / group_start
        ) * 100

        if diff_percent <= threshold_percent:
            current_group.append(horse)
        else:
            groups.append(current_group)
            current_group = [horse]
            group_start = value

    if current_group:
        groups.append(current_group)

    result = {}

    for i, group in enumerate(groups):
        score = (
            points_table[i]
            if i < len(points_table)
            else 0
        )

        for horse in group:
            result[horse["horse"]] = score

    return result


# =========================================================
# TABLES
# =========================================================

WIN_PERCENT_POINTS = [
    25, 22, 20, 17,
    14, 10, 6, 3
]

PLACE_PERCENT_POINTS = [
    20, 17, 15, 12,
    9, 5, 3, 2
]

PRIZE_MONEY_POINTS = [
    20, 17, 15, 13,
    11, 9, 6, 4
]


# =========================================================
# EQUIPMENT / WAGON
# =========================================================

def count_american_wagon_last_5(history):
    count = 0

    for race in history[:5]:
        raw = race.get("raw", "")

        if "Amerikansk" in raw:
            count += 1

    return count


def get_wagon_score(horse):
    current_equipment = horse.get("equipment", "")

    if current_equipment != "Amerikansk":
        return 0

    american_count = count_american_wagon_last_5(
        horse.get("history", [])
    )

    if american_count <= 1:
        return 10

    return 0


# =========================================================
# PRIZE MONEY
# =========================================================

def extract_prize_money(horse):
    raw = horse.get("raw", "")

    match = re.search(
        r"(\d[\d ]+)\s+\d+%",
        raw
    )

    if not match:
        return 0

    money_text = match.group(1)
    money_text = money_text.replace(" ", "")

    try:
        return int(money_text)
    except:
        return 0


# =========================================================
# ODDS
# =========================================================

def is_time_token(token):
    token = token.strip().replace(" ", "")

    return re.match(
        r"^\d{1,2},\d[a-zA-Z]*$",
        token
    ) is not None


def is_decimal_token(token):
    return re.match(
        r"^\d{1,3},\d{1,2}$",
        token
    ) is not None


def extract_odds_from_history_row(raw):
    parts = split_history_parts(raw)

    for part in reversed(parts):
        clean = part.replace(" ", "")

        if is_decimal_token(clean):
            try:
                return float(
                    clean.replace(",", ".")
                )
            except:
                pass

    return None


def calculate_avg_odds(history):
    odds_values = []

    for race in history[:5]:
        raw = race.get("raw", "")
        odds = extract_odds_from_history_row(raw)

        if odds is not None:
            odds_values.append(odds)

    if not odds_values:
        return None

    avg = sum(odds_values) / len(odds_values)

    return round(avg, 2)


def get_avg_odds_score(avg_odds):
    if avg_odds is None:
        return 0

    odds = avg_odds * 10

    if 10 <= odds <= 39:
        return 20
    if 40 <= odds <= 59:
        return 16
    if 60 <= odds <= 79:
        return 12
    if 80 <= odds <= 99:
        return 8
    if 100 <= odds <= 150:
        return 5

    return 2


# =========================================================
# DISTANCE ADDITION
# =========================================================

def get_distance_addition_score(horse, race):
    horse_distance = horse.get(
        "distance",
        race["distance"]
    )

    race_distance = race["distance"]

    if horse_distance <= race_distance:
        return 0

    additions = (
        horse_distance - race_distance
    ) // 20

    if additions <= 0:
        return 0

    norm = normalize_distance(race_distance)

    if norm == 1640:
        penalty = -15
    elif norm == 2140:
        penalty = -10
    else:
        penalty = -5

    return additions * penalty


# =========================================================
# GENDER
# =========================================================

def get_gender_score(horse, horses):
    gender = horse.get("gender", "")

    if gender != "s":
        return 0

    mixed = any(
        h.get("gender") in ["h", "v"]
        for h in horses
    )

    if mixed:
        return -10

    return 0


# =========================================================
# GALLOPS
# =========================================================

def count_gallops(history):
    count = 0

    for race in history[:5]:
        raw = race.get("raw", "").lower()
        parts = split_history_parts(raw)

        for part in parts:
            clean = part.strip().lower().replace(" ", "")

            if is_time_token(clean) and "g" in clean:
                count += 1
                break

            if clean in [
                "g",
                "galopp",
                "dg",
                "ug",
                "ag",
                "uag"
            ]:
                count += 1
                break

    return count


def get_gallop_score(history):
    if count_gallops(history) >= 2:
        return -10

    return 0


# =========================================================
# DYNAMIC SCORES
# =========================================================

def add_dynamic_scores(horses, race):
    target_distance = normalize_distance(
        race["distance"]
    )

    target_auto = race["start"] == "auto"

    speed_input = []

    for horse in horses:
        avg_time = calculate_avg_time(
            history=horse["history"],
            target_distance=target_distance,
            target_auto=target_auto
        )

        horse["avg_time"] = avg_time

        if avg_time is not None:
            speed_input.append({
                "horse": horse["horse"],
                "avg_time": avg_time
            })

    speed_map = speed_score_from_avg_times(
        speed_input
    )

    for horse in horses:
        horse["speed_score"] = speed_map.get(
            horse["horse"],
            0
        )

        stats = extract_stats_string(
            horse.get("raw", "")
        )

        if stats:
            starts = stats["starts"]
            wins = stats["wins"]
            seconds = stats["seconds"]
            thirds = stats["thirds"]
        else:
            starts = 0
            wins = 0
            seconds = 0
            thirds = 0

        horse["starts"] = starts

        if starts > 0:
            horse["win_percent"] = round(
                (wins / starts) * 100,
                1
            )

            horse["place_percent"] = round(
                (
                    (wins + seconds + thirds)
                    / starts
                ) * 100,
                1
            )
        else:
            horse["win_percent"] = 0
            horse["place_percent"] = 0

        horse["prize_money"] = extract_prize_money(horse)

        horse["avg_odds"] = calculate_avg_odds(
            horse["history"]
        )

    win_map = grouped_absolute_scores(
        horses,
        "win_percent",
        WIN_PERCENT_POINTS,
        2
    )

    place_map = grouped_absolute_scores(
        horses,
        "place_percent",
        PLACE_PERCENT_POINTS,
        2
    )

    money_map = grouped_relative_scores(
        horses,
        "prize_money",
        PRIZE_MONEY_POINTS,
        4
    )

    for horse in horses:
        horse["win_score"] = win_map.get(
            horse["horse"],
            0
        )

        horse["place_score"] = place_map.get(
            horse["horse"],
            0
        )

        horse["prize_money_score"] = money_map.get(
            horse["horse"],
            0
        )

        horse["avg_odds_score"] = get_avg_odds_score(
            horse["avg_odds"]
        )

        horse["latest_start_score"] = get_latest_start_score(
            horse["history"]
        )

        horse["distance_addition_score"] = get_distance_addition_score(
            horse,
            race
        )

        horse["gender_score"] = get_gender_score(
            horse,
            horses
        )

        horse["gallop_score"] = get_gallop_score(
            horse["history"]
        )

        horse["wagon_score"] = get_wagon_score(
            horse
        )

        horse["shoe_score"] = get_shoe_score(
            horse
        )

    return horses


# =========================================================
# TOTAL
# =========================================================

def calculate_total_score(
    horse,
    race,
    track_points
):
    total = (
        horse["speed_score"] +
        get_form_score(horse["history"]) +
        get_post_score(
            horse["post"],
            race,
            track_points
        ) +
        get_driver_score(
            horse["driver"]
        ) +
        get_record_score(
            horse["record"]
        ) +
        get_starts_score(
            horse["starts"]
        ) +
        horse["wagon_score"] +
        horse["shoe_score"] +
        horse["latest_start_score"] +
        horse["win_score"] +
        horse["place_score"] +
        horse["prize_money_score"] +
        horse["avg_odds_score"] +
        horse["distance_addition_score"] +
        horse["gender_score"] +
        horse["gallop_score"]
    )

    return int(total)


# =========================================================
# LABEL
# =========================================================

def get_label(rank, horse):
    percent = horse["percent"]

    if rank == 1:
        return "A"

    if rank <= 3:
        return "B"

    if percent <= 5:
        return "SKRÄLL"

    return "C"


# =========================================================
# FORMAT
# =========================================================

def format_decimal(value):
    if value is None:
        return "-"

    return str(value).replace(".", ",")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    track_points = load_track_points()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        raw_data = f.read()

    races = parse_input(raw_data)

    for race_data in races:
        race = race_data["race"]
        horses = race_data["horses"]

        horses = add_dynamic_scores(
            horses,
            race
        )

        ranked = []

        for horse in horses:
            horse["total_score"] = calculate_total_score(
                horse,
                race,
                track_points
            )

            ranked.append(horse)

        ranked = sorted(
            ranked,
            key=lambda x: x["total_score"],
            reverse=True
        )

        print()
        print("=" * 230)

        print(
            f"V86 Avdelning {race['race_no']} "
            f"- {race['track']} "
            f"{race['distance']}m "
            f"{race['start']}"
        )

        print("=" * 230)

        for i, horse in enumerate(ranked, start=1):
            label = get_label(i, horse)

            print(
                f"{i:>2}. "
                f"[{label:<7}] "
                f"{horse['horse']:<26} "
                f"Tot:{horse['total_score']:<4} "
                f"| Spd {horse['speed_score']:<2} "
                f"Form {get_form_score(horse['history']):<3} "
                f"Sen {horse['latest_start_score']:<2} "
                f"| Spår {get_post_score(horse['post'], race, track_points):<2} "
                f"Kusk {get_driver_score(horse['driver']):<2} "
                f"Rek {get_record_score(horse['record']):<2} "
                f"| Start {get_starts_score(horse['starts']):<3} "
                f"V% {horse['win_score']:<2} "
                f"P% {horse['place_score']:<2} "
                f"| Pris {horse['prize_money_score']:<2} "
                f"Odds {horse['avg_odds_score']:<2} "
                f"| Vagn {horse['wagon_score']:<2} "
                f"Skor {horse['shoe_score']:<2} "
                f"| Till {horse['distance_addition_score']:<3} "
                f"Kön {horse['gender_score']:<3} "
                f"Gal {horse['gallop_score']:<3}"
            )

            print(
                f"    AvgTid: {format_decimal(horse['avg_time']):<6} "
                f"Snittodds: {format_decimal(horse['avg_odds']):<6} "
                f"Prissumma: {horse['prize_money']:<9} "
                f"Starter: {horse['starts']:<3} "
                f"Seger%: {horse['win_percent']:<5} "
                f"Plats%: {horse['place_percent']:<5} "
                f"Vagn idag: {horse['equipment']:<10} "
                f"Kusk: {horse['driver']}"
            )

            print("-" * 230)