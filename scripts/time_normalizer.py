# time_normalizer.py

# -------------------------------------------------
# START METHOD ADJUSTMENT
# -------------------------------------------------

START_METHOD_ADJUST = {
    "volt_to_auto": {
        "1600": -1.0,
        "2100": -0.7,
        "2600": -0.5,
        "3100": -0.4
    },
    "auto_to_volt": {
        "1600": +1.0,
        "2100": +0.7,
        "2600": +0.5,
        "3100": +0.4
    }
}

# -------------------------------------------------
# DISTANCE ADJUSTMENT (BASELINE = CURRENT DISTANCE)
# -------------------------------------------------

DISTANCE_ADJUST = {
    "1600": {
        "2100": -0.9,
        "2600": -1.6,
        "3100": -2.1
    },
    "2100": {
        "1600": +0.9,
        "2600": -0.7,
        "3100": -1.2
    },
    "2600": {
        "1600": +1.6,
        "2100": +0.7,
        "3100": -0.4
    },
    "3100": {
        "1600": +2.1,
        "2100": +1.2,
        "2600": +0.5
    }
}


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def parse_time(time_str: str):
    """
    Converts '14,5a' -> (14.5, suffix)
    """

    if not time_str or time_str == "None":
        return None, None

    time_str = time_str.lower().replace(",", ".")

    value = ""
    suffix = ""

    for c in time_str:
        if c.isdigit() or c == ".":
            value += c
        else:
            suffix += c

    try:
        return float(value), suffix
    except:
        return None, None


# -------------------------------------------------
# MAIN NORMALIZATION FUNCTION
# -------------------------------------------------

def normalize_time(raw_time, start_type, race_distance, current_distance):

    """
    raw_time: "14,5a"
    start_type: "auto" or "volt"
    race_distance: "2100"
    current_distance: "1600"
    """

    base_time, suffix = parse_time(raw_time)

    if base_time is None:
        return None

    # -------------------------
    # 1. START METHOD ADJUST
    # -------------------------

    start_key = f"{race_distance}"

    if start_type == "volt":
        adjusted = START_METHOD_ADJUST["volt_to_auto"].get(start_key, 0)
    else:
        adjusted = START_METHOD_ADJUST["auto_to_volt"].get(start_key, 0)

    base_time += adjusted

    # -------------------------
    # 2. DISTANCE ADJUST
    # -------------------------

    dist_map = DISTANCE_ADJUST.get(current_distance, {})

    dist_adjust = dist_map.get(race_distance, 0)

    base_time += dist_adjust

    # -------------------------
    # OUTPUT
    # -------------------------

    return {
        "normalized_time": round(base_time, 2),
        "raw_time": raw_time,
        "suffix": suffix
    }