# =========================================================
# RANKING ENGINE V3 - JSON CONFIG VERSION
# =========================================================

import json
import re

from rank68_badge_helpers import apply_rank68_badges, remove_old_top5_badges

from scripts.speed_feature import (
    calculate_avg_time,
    normalize_distance,
    speed_score_from_avg_times,
    parse_time_token,
    normalize_time
)

from scripts.speed_ranking import speed_score
from scripts.parser_v2 import parse_input
from datetime import datetime

from badge_rules import (
    get_race_metrics,
    get_loppbadge,
    format_loppbadge
)

def get_inactivity_score(horse):
    history = horse.get("history", [])

    if not history:
        return 0

    latest_start = history[0]
    latest_date = latest_start.get("date", "")

    if not latest_date:
        return 0

    try:
        latest_date_obj = datetime.strptime(latest_date, "%Y-%m-%d")
        today = datetime.today()

        days_since_start = (today - latest_date_obj).days

        if days_since_start > 60:
            return -10

        return 0

    except:
        return 0


# =========================================================
# PATHS
# =========================================================

INPUT_PATH = "input/input_word_new.txt"

TRACK_POINTS_PATH = "config/track_points.json"
DRIVER_POINTS_PATH = "config/driver_points.json"
MANUAL_POINTS_PATH = "config/manual_points.json"
SCORING_RULES_PATH = "config/scoring_rules.json"


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
DRIVER_STATS_PATH = "config/driver_stats.json"

with open(DRIVER_STATS_PATH, "r", encoding="utf-8") as f:
    driver_stats = json.load(f)

track_points = load_json(TRACK_POINTS_PATH)
driver_points = load_json(DRIVER_POINTS_PATH)
manual_points = load_json(MANUAL_POINTS_PATH)
scoring_rules = load_json(SCORING_RULES_PATH)


# =========================================================
# HELPERS
# =========================================================

def split_history_parts(raw):
    return [
        p.strip()
        for p in raw.split("\t")
        if p.strip()
    ]


def format_decimal(value):
    if value is None:
        return "-"

    return str(value).replace(".", ",")


def get_track_distance_group(distance):
    if 1609 <= distance <= 1680:
        return "1600"

    if 2100 <= distance <= 2200:
        return "2100"

    if 2600 <= distance <= 3200:
        return "2600"

    if distance < 1900:
        return "1600"

    if distance < 2500:
        return "2100"

    return "2600"


def is_time_token(token):
    token = token.strip().replace(" ", "")

    return re.match(
        r"^\d{1,2},\d[a-zA-Z]*$",
        token
    ) is not None


def is_decimal_token(token):
    token = token.strip().replace(" ", "")

    return re.match(
        r"^\d{1,3},\d{1,2}$",
        token
    ) is not None


def parse_decimal_comma(value):
    try:
        return float(value.replace(",", "."))
    except:
        return None


# =========================================================
# DRIVER / MANUAL
# =========================================================

def get_driver_score(driver):

    driver_name = driver.split("(")[0].strip()

    if driver_name not in driver_stats:
        return 0

    stats = driver_stats[driver_name]

    starts = stats.get("starts", 0)
    win_percent = stats.get("win_percent", 0)

    # Inställningar från sidebar
    min_starts = scoring_rules.get(
        "driver_min_starts",
        70
    )

    mid_starts = scoring_rules.get(
        "driver_mid_starts",
        150
    )

    high_starts = scoring_rules.get(
        "driver_high_starts",
        300
    )

    low_multiplier = scoring_rules.get(
        "driver_low_multiplier",
        0.75
    )

    mid_multiplier = scoring_rules.get(
        "driver_mid_multiplier",
        1.0
    )

    high_multiplier = scoring_rules.get(
        "driver_high_multiplier",
        1.25
    )

    # Minsta antal lopp
    if starts < min_starts:
        return 0

    # Grundpoäng
    if win_percent >= 19:
        base_score = 12

    elif win_percent >= 16:
        base_score = 9

    elif win_percent >= 13:
        base_score = 6

    elif win_percent >= 10:
        base_score = 3

    else:
        base_score = 0

    # Multiplier
    if starts >= high_starts:
        multiplier = high_multiplier

    elif starts >= mid_starts:
        multiplier = mid_multiplier

    else:
        multiplier = low_multiplier

    return round(base_score * multiplier)

def get_driver_change_score(horse):
    current_driver = horse.get("driver", "")
    current_score = get_driver_score(current_driver)

    history = horse.get("history", [])[:5]

    if not history:
        return 0

    better_count = 0
    compared_count = 0

    for race in history:
        previous_driver = race.get("driver", "")

        if not previous_driver:
            continue

        previous_score = get_driver_score(previous_driver)
        compared_count += 1

        if current_score > previous_score:
            better_count += 1

    if compared_count == 0:
        return 0

    if better_count >= 4:
        return 10

    if better_count == 3:
        return 6

    return 0


def get_shoe_score(horse):
    return manual_points.get(
        "shoes",
        {}
    ).get(
        horse["horse"],
        0
    )


def get_custom_score(horse):
    return manual_points.get(
        "custom",
        {}
    ).get(
        horse["horse"],
        0
    )


# =========================================================
# POST / TRACK POINTS
# =========================================================

def get_post_score(post, race):
    distance_group = get_track_distance_group(
        race["distance"]
    )

    key = f"{distance_group}_{race['start']}"

    points = track_points.get(key)

    if not points:
        return 0

    if post <= 0:
        return 0

    index = post - 1

    if index >= len(points):
        return points[-1]

    return points[index]


# =========================================================
# FORM
# =========================================================

def get_form_score(history):
    if not history:
        return 0

    score = 0

    form_points = scoring_rules.get(
        "form_points",
        {}
    )

    track_form_points = scoring_rules.get(
        "track_form_points",
        {}
    )

    for race in history[:5]:
        raw = race.get("raw", "")
        parts = split_history_parts(raw)

        if len(parts) < 3:
            continue

        placement = parts[2].strip().lower()

        score += form_points.get(
            placement,
            0
        )

        track_part = parts[0].strip()

        for track_name, bonus in track_form_points.items():
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

    placement = parts[2].strip().lower()

    return scoring_rules.get(
        "latest_start_points",
        {}
    ).get(
        placement,
        0
    )


# =========================================================
# RECORD
# =========================================================

def record_to_float(record):
    if not record:
        return None

    try:
        cleaned = record

        for token in [
            "aK",
            "aM",
            "aL",
            "a",
            "K",
            "M",
            "L",
            "g"
        ]:
            cleaned = cleaned.replace(
                token,
                ""
            )

        cleaned = cleaned.replace(",", ".")
        cleaned = cleaned.replace(" ", "")

        return float(cleaned)

    except:
        return None


def get_record_score(record):
    value = record_to_float(record)

    if value is None:
        return 0

    for row in scoring_rules.get(
        "record_points",
        []
    ):
        if value <= row["max"]:
            return row["points"]

    return 0

def record_score_from_records(
    horses,
    target_distance,
    target_auto
):

    valid = []

    for horse in horses:

        record = horse.get("record")

        parsed = parse_time_token(record)

        if not parsed:
            continue

        normalized = normalize_time(
            historical_time=parsed["time"],
            historical_distance=target_distance,
            historical_auto=parsed["auto"],
            historical_gallop=parsed["gallop"],
            target_distance=target_distance,
            target_auto=target_auto
        )

        valid.append({
            "horse": horse["horse"],
            "record_time": normalized
        })

    sorted_h = sorted(
        valid,
        key=lambda x: x["record_time"]
    )

    threshold = 0.1

    groups = []

    current_group = []

    current_group_start = None

    for h in sorted_h:

        if not current_group:

            current_group = [h]

            current_group_start = h["record_time"]

            continue

        diff = round(
            h["record_time"] - current_group_start,
            2
        )

        if diff <= threshold:

            current_group.append(h)

        else:

            groups.append(current_group)

            current_group = [h]

            current_group_start = h["record_time"]

    if current_group:
        groups.append(current_group)

    scores = [24, 22, 20, 17, 15, 13, 10, 8]

    result = {}

    for i, group in enumerate(groups):

        score = scores[i] if i < len(scores) else 1

        for h in group:

            result[h["horse"]] = score

    return result

# =========================================================
# STARTS / WIN% / PLACE%
# =========================================================

def extract_stats_string(raw_text):
    match = re.search(
        r"\b(\d+)-(\d+)-(\d+)\b",
        raw_text
    )

    if not match:
        return None

    first_part = match.group(1)
    second_part = int(match.group(2))
    third_part = int(match.group(3))

    # Standard ATG-format, t.ex:
    # 254-7-4 = 25 starter, 4 segrar, 7 andraplatser, 4 tredjeplatser
    if len(first_part) >= 4:
        starts = int(first_part[:-2])
        wins = int(first_part[-2:])
        seconds = second_part
        thirds = third_part

    elif len(first_part) >= 2:
        starts = int(first_part[:-1])
        wins = int(first_part[-1])
        seconds = second_part
        thirds = third_part

    else:
        starts = int(first_part)
        wins = 0
        seconds = second_part
        thirds = third_part

    # Specialfall:
    # 10-10-0 ska tolkas som 10 starter, 10 segrar, 0 andraplatser, 0 tredjeplatser
    # om den vanliga tolkningen blir orimlig.
    if wins + seconds + thirds > starts:
        starts = int(first_part)
        wins = second_part
        seconds = third_part
        thirds = 0

    

    return {
        "starts": starts,
        "wins": wins,
        "seconds": seconds,
        "thirds": thirds
    }

def get_starts_score(starts):
    if starts <= 0:
        return 0

    for row in scoring_rules.get(
        "starts_points",
        []
    ):
        if row["min"] <= starts <= row["max"]:
            return row["points"]

    return 0


# =========================================================
# GROUP SCORING
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
    current_group_start = None

    for horse in sorted_horses:
        value = horse[value_key]

        if not current_group:
            current_group = [horse]
            current_group_start = value
            continue

        diff = current_group_start - value

        if diff <= threshold:
            current_group.append(horse)
        else:
            groups.append(current_group)
            current_group = [horse]
            current_group_start = value

    if current_group:
        groups.append(current_group)

    result = {}

    for i, group in enumerate(groups):
        score = points_table[i] if i < len(points_table) else 0

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

        if value is not None and value > 0:
            valid.append(horse)

    sorted_horses = sorted(
        valid,
        key=lambda x: x[value_key],
        reverse=True
    )

    groups = []
    current_group = []
    current_group_start = None

    for horse in sorted_horses:
        value = horse[value_key]

        if not current_group:
            current_group = [horse]
            current_group_start = value
            continue

        diff_percent = (
            (current_group_start - value)
            / current_group_start
        ) * 100

        if diff_percent <= threshold_percent:
            current_group.append(horse)
        else:
            groups.append(current_group)
            current_group = [horse]
            current_group_start = value

    if current_group:
        groups.append(current_group)

    result = {}

    for i, group in enumerate(groups):
        score = points_table[i] if i < len(points_table) else 0

        for horse in group:
            result[horse["horse"]] = score

    return result


# =========================================================
# PRIZE MONEY
# =========================================================

def extract_prize_money(horse):
    raw = horse.get("raw", "")
    lines = [
        line.strip()
        for line in raw.split("\n")
        if line.strip()
    ]

    if len(lines) < 2:
        return 0

    info_line = lines[1]

    match = re.search(
        r"\d{4}\s*:\s*\d+\s+([0-9 ]+?)\s+\d+%",
        info_line
    )

    if not match:
        return 0

    money_text = match.group(1).replace(" ", "")

    try:
        return int(money_text)
    except:
        return 0


# =========================================================
# AVG ODDS
# =========================================================

def extract_odds_from_history_row(raw):
    parts = split_history_parts(raw)

    time_index = None

    for i, part in enumerate(parts):
        if is_time_token(part):
            time_index = i
            break

    if time_index is None:
        return None

    for part in parts[time_index + 1:]:
        clean = part.strip().replace(" ", "")

        if clean in [
            "--",
            "-"
        ]:
            continue

        if is_decimal_token(clean):
            return parse_decimal_comma(clean)

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

    odds_index = avg_odds * 10

    for row in scoring_rules.get(
        "avg_odds_ranges",
        []
    ):
        if row["min"] <= odds_index <= row["max"]:
            return row["points"]

    return 0


# =========================================================
# DISTANCE ADDITION
# =========================================================

def get_distance_addition_score(horse, race):
    horse_distance = horse.get("distance", 0)
    race_distance = race.get("distance", 0)

    if horse_distance <= race_distance:
        return 0

    extra_meters = horse_distance - race_distance
    additions = extra_meters // 20

    if additions <= 0:
        return 0

    distance_group = normalize_distance(race_distance)

    penalty_map = scoring_rules.get(
        "distance_addition_penalty",
        {}
    )

    if distance_group == 1640:
        penalty = penalty_map.get("1640", 0)
    elif distance_group == 2140:
        penalty = penalty_map.get("2140", 0)
    else:
        penalty = penalty_map.get("2640", 0)

    return int(additions * penalty)


# =========================================================
# GENDER
# =========================================================

def get_gender_score(horse, horses):
    gender = horse.get("gender", "")

    if gender != "s":
        return 0

    mixed = any(
        h.get("gender", "") in ["h", "v"]
        for h in horses
    )

    if mixed:
        return scoring_rules.get(
            "gender_penalty_sto_mixed",
            0
        )

    return 0


# =========================================================
# GALLOP
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
    gallops = count_gallops(history)

    min_count = scoring_rules.get(
        "gallop_penalty_min_count",
        2
    )

    if gallops >= min_count:
        return scoring_rules.get(
            "gallop_penalty",
            0
        )

    return 0


# =========================================================
# WAGON / SHOES
# =========================================================

def count_american_wagon_last_5(history):
    count = 0

    for race in history[:5]:
        raw = race.get("raw", "")

        if "Amerikansk" in raw:
            count += 1

    return count


def get_wagon_score(horse):

    current_equipment = horse.get(
        "equipment",
        ""
    )

    equipment = current_equipment.lower().strip()

    if "amerikansk" not in equipment:
        return 0

    recent_count = count_american_wagon_last_5(
        horse.get("history", [])
    )

    max_recent_count = scoring_rules.get(
        "american_wagon_max_recent_count",
        1
    )

    if recent_count <= max_recent_count:
        return scoring_rules.get(
            "american_wagon_bonus",
            0
        )

    return 0


# =========================================================
# DYNAMIC SCORES
# =========================================================

# scripts/ranking_engine_v3.py
def get_recent_prize_score(history):
    total_prize = 0

    for start in history[:5]:
        raw = start.get("raw", "")

        match = re.search(r"(\d+)'", raw)

        if match:
            total_prize += int(match.group(1)) * 1000

    score = 0

    for row in scoring_rules.get("recent_prize_ranges", []):
        if total_prize >= row["min"]:
            score = row["points"]

    return score

def get_class_change_score(history):
    class_scores = []

    placement_factor = {
        "1": 1.0,
        "2": 0.8,
        "3": 0.65,
        "4": 0.45,
        "5": 0.3,
        "0": 0.1,
        "d": 0,
        "g": 0
    }

    for race in history[:5]:
        raw = race.get("raw", "")
        parts = split_history_parts(raw)

        if len(parts) < 3:
            continue

        placement = parts[2].strip().lower()

        prize_match = re.search(r"(\d+)'", raw)

        if not prize_match:
            continue

        prize = int(prize_match.group(1)) * 1000

        factor = placement_factor.get(placement, 0)

        if factor <= 0:
            continue

        class_scores.append({
            "prize": prize,
            "weighted": prize * factor
        })

    if len(class_scores) < 3:
        return 0

    high_class_count = sum(
        1 for row in class_scores
        if row["prize"] >= 100000
    )

    if high_class_count < 3:
        return 0

    avg_weighted = sum(
        row["weighted"] for row in class_scores
    ) / len(class_scores)

    if avg_weighted >= 200000:
        return 10

    if avg_weighted >= 125000:
        return 6

    if avg_weighted >= 100000:
        return 3

    return 0

def add_dynamic_scores(horses, race, **kwargs):

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

    speed_map = speed_score_from_avg_times(speed_input)

    record_score_map = record_score_from_records(
    horses,
    target_distance,
    target_auto
)

    for horse in horses:

        horse["speed_score"] = speed_map.get(horse["horse"], 0)

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
        horse["wins"] = wins
        horse["seconds"] = seconds
        horse["thirds"] = thirds

        if starts > 0:
            horse["win_percent"] = round((wins / starts) * 100, 1)
            horse["place_percent"] = round(
                ((wins + seconds + thirds) / starts) * 100,
                1
            )
        else:
            horse["win_percent"] = 0
            horse["place_percent"] = 0

        horse["prize_money"] = extract_prize_money(horse)
        horse["avg_odds"] = calculate_avg_odds(horse["history"])

    win_score_map = grouped_absolute_scores(
        horses,
        "win_percent",
        scoring_rules.get("win_percent_points", []),
        scoring_rules.get("win_percent_group_threshold", 2)
    )

    place_score_map = grouped_absolute_scores(
        horses,
        "place_percent",
        scoring_rules.get("place_percent_points", []),
        scoring_rules.get("place_percent_group_threshold", 2)
    )

    spel_score_map = grouped_absolute_scores(
        horses,
        "percent",
        scoring_rules.get("spel_percent_points", []),
        scoring_rules.get("spel_percent_group_threshold", 2)
    )

    prize_money_score_map = grouped_relative_scores(
        horses,
        "prize_money",
        scoring_rules.get("prize_money_points", []),
        scoring_rules.get("prize_money_group_threshold_percent", 4)
    )

    for horse in horses:

        horse["form_score"] = get_form_score(horse["history"])
        horse["latest_start_score"] = get_latest_start_score(horse["history"])
        horse["post_score"] = get_post_score(horse["post"], race)
        horse["driver_score"] = get_driver_score(horse["driver"])
        horse["driver_change_score"] = get_driver_change_score(horse)
        horse["record_score"] = record_score_map.get(
        horse["horse"],
        0
    )
        horse["starts_score"] = get_starts_score(horse["starts"])

        horse["win_score"] = win_score_map.get(horse["horse"], 0)
        horse["place_score"] = place_score_map.get(horse["horse"], 0)
        horse["spel_score"] = spel_score_map.get(horse["horse"], 0)
        horse["prize_money_score"] = prize_money_score_map.get(horse["horse"], 0)
        horse["avg_odds_score"] = get_avg_odds_score(horse["avg_odds"])
        horse["recent_prize_score"] = get_recent_prize_score(horse["history"])
        horse["class_change_score"] = get_class_change_score(horse["history"])
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

        horse["wagon_score"] = get_wagon_score(horse)
        horse["shoe_score"] = get_shoe_score(horse)
        horse["inactivity_score"] = get_inactivity_score(horse)
        horse["custom_score"] = get_custom_score(horse)

    return horses


# =========================================================
# TOTAL
# =========================================================

def calculate_total_score(horse):
    total = (
        horse["speed_score"] +
        horse["form_score"] +
        horse.get("stallform_score", 0) +
        horse["latest_start_score"] +
        horse["post_score"] +
        horse["driver_score"] +
        horse.get("driver_change_score", 0) +
        horse["record_score"] +
        horse["starts_score"] +
        horse["win_score"] +
        horse["place_score"] +
        horse.get("spel_score", 0) +
        horse["prize_money_score"] +
        horse.get("recent_prize_score", 0) +
        horse.get("class_change_score", 0) +
        horse["avg_odds_score"] +
        horse["distance_addition_score"] +
        horse["gender_score"] +
        horse["gallop_score"] +
        horse["wagon_score"] +
        horse["shoe_score"] +
        horse.get("inactivity_score", 0) +
        horse["custom_score"]
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
# MAIN
# =========================================================

if __name__ == "__main__":

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
                horse
            )

            ranked.append(horse)

        ranked = sorted(
            ranked,
            key=lambda x: x["total_score"],
            reverse=True
        )

        for idx, horse in enumerate(ranked, start=1):
            horse["model_rank"] = idx

        race_metrics = get_race_metrics(ranked)

        loppbadge = get_loppbadge(race_metrics)

        print()
        print("=" * 230)
        print()

        print(
            format_loppbadge(loppbadge)
        )

        print()

        print(
            f"V86 Avdelning {race['race_no']} "
            f"- {race['track']} "
            f"{race['distance']}m "
            f"{race['start']}"
        )

        print("=" * 230)

        for i, horse in enumerate(ranked, start=1):
            label = get_label(i, horse)
            badges = get_horse_badges(horse)
            h["badges"] = remove_old_top5_badges(h.get("badges", []))
            h = apply_rank68_badges(h)

            losers = get_loser_flags(
                horse,
                loppbadge
            )

            extra_badges = badges + losers

            badge_text = ""

            if extra_badges:
                badge_text = (
                    " ["
                    + " | ".join(extra_badges)
                    + "]"
                )

            print(
                f"{i:>2}. "
                f"[{label:<7}] "
                f"{horse['horse']:<26} "
                f"Tot:{horse['total_score']:<4} "
                f"| Spd {horse['speed_score']:<2} "
                f"Form {horse['form_score']:<3} "
                f"Sen {horse['latest_start_score']:<2} "
                f"| Spår {horse['post_score']:<2} "
                f"Kusk {horse['driver_score']:<2} "
                f"Rek {horse['record_score']:<2} "
                f"| Start {horse['starts_score']:<3} "
                f"V% {horse['win_score']:<2} "
                f"P% {horse['place_score']:<2} "
                f"| Pris {horse['prize_money_score']:<2} "
                f"Odds {horse['avg_odds_score']:<2} "
                f"| Vagn {horse['wagon_score']:<2} "
                f"Skor {horse['shoe_score']:<2} "
                f"Man {horse['custom_score']:<2} "
                f"| Till {horse['distance_addition_score']:<3} "
                f"Kön {horse['gender_score']:<3} "
                f"Gal {horse['gallop_score']:<3}"
                f"{badge_text}"
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