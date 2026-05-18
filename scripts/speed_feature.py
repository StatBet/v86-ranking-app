import re


# -------------------------------------------------
# DISTANCE NORMALIZATION TABLE
# -------------------------------------------------

DISTANCE_TABLE = {
    1640: {
        1640: 0.0,
        2140: 0.9,
        2640: 1.6,
        3140: 2.1
    },

    2140: {
        1640: -0.9,
        2140: 0.0,
        2640: 0.7,
        3140: 1.2
    },

    2640: {
        1640: -1.6,
        2140: -0.7,
        2640: 0.0,
        3140: 0.5
    },

    3140: {
        1640: -2.1,
        2140: -1.2,
        2640: -0.5,
        3140: 0.0
    }
}


# -------------------------------------------------
# VOLT VS AUTO TABLE
# volt slower than auto
# -------------------------------------------------

START_TABLE = {
    1640: 1.0,
    2140: 0.7,
    2640: 0.5,
    3140: 0.4
}


# -------------------------------------------------
# DISTANCE GROUP
# -------------------------------------------------

def normalize_distance(distance):

    if distance <= 1900:
        return 1640

    if distance <= 2400:
        return 2140

    if distance <= 2900:
        return 2640

    return 3140


# -------------------------------------------------
# PARSE TIME TOKEN
# examples:
# 12,1aK
# 13,5g
# 14,0ag
# -------------------------------------------------

def parse_time_token(token):

    if not token:
        return None

    token = token.strip().replace(" ", "")

    match = re.match(
        r"^(\d{1,2},\d)([a-zA-Z]*)$",
        token
    )

    if not match:
        return None

    time_value = float(
        match.group(1).replace(",", ".")
    )

    suffix = match.group(2).lower()

    return {
        "time": time_value,
        "auto": "a" in suffix,
        "gallop": "g" in suffix,
        "raw": token,
    }


# -------------------------------------------------
# EXTRACT DISTANCE
# -------------------------------------------------

def extract_distance_from_token(token):

    match = re.search(r"(\d{4})", token)

    if not match:
        return None

    return int(match.group(1))


# -------------------------------------------------
# EXTRACT TIME + DISTANCE FROM HISTORY
# -------------------------------------------------

def extract_time_and_distance_from_history(raw):

    parts = [
        p.strip()
        for p in raw.split("\t")
        if p.strip()
    ]

    distance_index = None

    historical_distance = None

    for i, part in enumerate(parts):

        distance = extract_distance_from_token(part)

        if distance:

            historical_distance = normalize_distance(
                distance
            )

            distance_index = i

            break

    if distance_index is None:
        return None

    for part in parts[distance_index + 1:]:

        parsed_time = parse_time_token(part)

        if parsed_time:

            return {
                "time": parsed_time["time"],
                "historical_distance": historical_distance,
                "historical_auto": parsed_time["auto"],
                "historical_gallop": parsed_time["gallop"],
                "raw_time": parsed_time["raw"],
            }

    return None


# -------------------------------------------------
# NORMALIZE TIME
# convert historical race
# -> today's race conditions
# -------------------------------------------------

def normalize_time(
    historical_time,
    historical_distance,
    historical_auto,
    historical_gallop,
    target_distance,
    target_auto
):

    time = historical_time

    # ---------------------------------------------
    # GALLOP BONUS
    # ---------------------------------------------

    if historical_gallop:
        time -= 0.4

    # ---------------------------------------------
    # DISTANCE NORMALIZATION
    # ---------------------------------------------

    dist_adjustment = DISTANCE_TABLE[
        historical_distance
    ][
        target_distance
    ]

    time += dist_adjustment

    # ---------------------------------------------
    # START METHOD NORMALIZATION
    # volt slower than auto
    # ---------------------------------------------

    if historical_auto != target_auto:

        adjustment = START_TABLE[target_distance]

        # historical volt -> target auto
        if not historical_auto and target_auto:

            time -= adjustment

        # historical auto -> target volt
        elif historical_auto and not target_auto:

            time += adjustment

    return round(time, 2)


# -------------------------------------------------
# CALCULATE AVG TIME
# -------------------------------------------------

def calculate_avg_time(
    history,
    target_distance,
    target_auto
):

    normalized_times = []

    for race in history:

        raw = race.get("raw", "")

        extracted = extract_time_and_distance_from_history(
            raw
        )

        if not extracted:
            continue

        normalized = normalize_time(
            historical_time=extracted["time"],
            historical_distance=extracted["historical_distance"],
            historical_auto=extracted["historical_auto"],
            historical_gallop=extracted["historical_gallop"],
            target_distance=target_distance,
            target_auto=target_auto
        )

        normalized_times.append(normalized)

    if not normalized_times:
        return None

    avg = sum(normalized_times) / len(normalized_times)

    return round(avg, 2)


# -------------------------------------------------
# SPEED SCORE SYSTEM
# -------------------------------------------------

def speed_score_from_avg_times(horses):

    valid = []

    for h in horses:

        if h["avg_time"] is not None:

            valid.append(h)

    sorted_h = sorted(
        valid,
        key=lambda x: x["avg_time"]
    )

    # -------------------------------------------------
    # GROUPING
    # compare against FIRST value in group
    # -------------------------------------------------

    threshold = 0.1

    groups = []

    current_group = []

    current_group_start = None

    for h in sorted_h:

        # ---------------------------------------------
        # FIRST HORSE
        # ---------------------------------------------

        if not current_group:

            current_group = [h]

            current_group_start = h["avg_time"]

            continue

        # ---------------------------------------------
        # DIFF AGAINST GROUP START
        # ---------------------------------------------

        diff = round(
            h["avg_time"] - current_group_start,
            2
        )

        # SAME GROUP
        if diff <= threshold:

            current_group.append(h)

        # NEW GROUP
        else:

            groups.append(current_group)

            current_group = [h]

            current_group_start = h["avg_time"]

    if current_group:

        groups.append(current_group)

    # -------------------------------------------------
    # SPEED POINTS
    # -------------------------------------------------

    scores = [24, 22, 20, 17, 15, 13, 10, 8]

    result = {}

    for i, group in enumerate(groups):

        if i < len(scores):

            score = scores[i]

        else:

            score = 1

        for h in group:

            result[h["horse"]] = score

    return result