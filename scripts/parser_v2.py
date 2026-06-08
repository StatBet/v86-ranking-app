import re


# -------------------------------------------------
# CLEAN HELPERS
# -------------------------------------------------

def clean(line: str):
    return line.strip()


# -------------------------------------------------
# EXTRACT TRACK
# -------------------------------------------------

def extract_track(lines):

    for line in lines:

        line = clean(line)

        if not line:
            continue

        if "Avdelning" in line:
            continue

        if "Trav" in line:
            continue

        if "•" in line:
            continue

        if "m" in line and any(char.isdigit() for char in line):
            continue

        if "idag" in line.lower():
            continue

        if "autostart" in line.lower():
            continue

        if "volt" in line.lower():
            continue

        if line and line[0].isalpha():
            return line

    return "UNKNOWN"


# -------------------------------------------------
# EXTRACT RACE NUMBER
# -------------------------------------------------

def extract_race_no(lines):

    for line in lines:

        match = re.search(r"Avdelning\s+(\d+)", line)

        if match:
            return int(match.group(1))

    return 0


# -------------------------------------------------
# EXTRACT DISTANCE
# -------------------------------------------------

def extract_distance(text):

    match = re.search(r"(\d{4})\s*m", text)

    if match:
        return int(match.group(1))

    return 0


# -------------------------------------------------
# EXTRACT START TYPE
# -------------------------------------------------

def extract_start_type(text):

    text = text.lower()

    if "autostart" in text:
        return "auto"

    if "volt" in text:
        return "volt"

    return "unknown"


# -------------------------------------------------
# BUILD RACE OBJECT
# -------------------------------------------------

def parse_race_header(header_text):

    lines = header_text.split("\n")

    track = extract_track(lines)
    race_no = extract_race_no(lines)
    distance = extract_distance(header_text)
    start = extract_start_type(header_text)

    race_id = f"{track}|A{race_no}|{distance}|{start}"

    return {
        "track": track,
        "race_no": race_no,
        "distance": distance,
        "start": start,
        "race_id": race_id
    }


# -------------------------------------------------
# PARSE HISTORY
# -------------------------------------------------

def parse_history(lines):

    history = []

    i = 0

    while i < len(lines):

        line = lines[i]

        if re.match(r"\d{4}-\d{2}-\d{2}", line):

            date = line

            if i + 1 < len(lines):

                race_line = lines[i + 1]

                history.append({
                    "date": date,
                    "raw": race_line
                })

            i += 2

        else:
            i += 1

    return history


# -------------------------------------------------
# PARSE HORSE BLOCK
# -------------------------------------------------

def parse_horse_block(block):

    lines = [line.strip() for line in block.split("\n") if line.strip()]

    if len(lines) < 2:
        return None

    name_line = lines[0]
    info_line = lines[1]

    if "Senaste 5 starterna" in name_line:
        return None

    if "Formrader" in name_line:
        return None

    if "VIDEO" in name_line:
        return None

    # ---------------------------------------------
    # NAME / AGE / GENDER
    # ---------------------------------------------

    name_match = re.match(r"(.+?)([vhs])(\d+)$", name_line)

    if name_match:

        horse_name = name_match.group(1).strip()
        gender = name_match.group(2)
        age = int(name_match.group(3))

    else:

        horse_name = name_line
        gender = ""
        age = 0

    # ---------------------------------------------
    # DRIVER
    # ---------------------------------------------

    driver_match = re.match(r"(.+?)\(", info_line)

    driver = driver_match.group(1).strip() if driver_match else ""

    # ---------------------------------------------
    # STRECK %
    # ---------------------------------------------

    percent_match = re.search(r"(\d+)%", info_line)

    percent = int(percent_match.group(1)) if percent_match else 0

    # ---------------------------------------------
    # DISTANCE + POST
    # ---------------------------------------------

    post_match = re.search(r"(\d{4})\s*:\s*(\d+)", info_line)

    if post_match:

        distance = int(post_match.group(1))
        post = int(post_match.group(2))

    else:

        distance = 0
        post = 0

    # ---------------------------------------------
    # EQUIPMENT
    # ---------------------------------------------

    equipment = ""

    if "Amerikansk" in info_line:
        equipment = "Amerikansk"

    elif "Vanlig" in info_line:
        equipment = "Vanlig"

    # ---------------------------------------------
    # RECORD
    # ---------------------------------------------

    record_match = re.search(r"(\d{1,2},\d[a-zA-Z]*)$", info_line)

    record = record_match.group(1) if record_match else ""

    # ---------------------------------------------
    # HISTORY
    # ---------------------------------------------

    history = parse_history(lines[2:])

    return {
        "horse": horse_name,
        "gender": gender,
        "age": age,
        "driver": driver,
        "percent": percent,
        "distance": distance,
        "post": post,
        "equipment": equipment,
        "record": record,
        "history": history,
        "raw": block
    }


# -------------------------------------------------
# SPLIT HORSE BLOCKS
# -------------------------------------------------

def split_horse_blocks(race_text):

    lines = race_text.split("\n")

    blocks = []

    current = []

    horse_start_pattern = re.compile(r".+[vhs]\d+$")

    for line in lines:

        stripped = line.strip()

        if horse_start_pattern.match(stripped):

            if current:
                blocks.append("\n".join(current))
                current = []

        if stripped:
            current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


# -------------------------------------------------
# PARSE INPUT
# -------------------------------------------------

def parse_input(raw_data):

    races = []

    race_chunks = re.split(r"(?=Avdelning\s+\d+)", raw_data)

    for chunk in race_chunks:

        if not chunk.strip():
            continue

        if "Avdelning" not in chunk:
            continue

        parts = chunk.split("DISTANS & SPÅR", 1)

        header_text = parts[0]

        horses_text = parts[1] if len(parts) > 1 else ""

        race = parse_race_header(header_text)

        horse_blocks = split_horse_blocks(horses_text)

        horses = []

        for block in horse_blocks:

            horse = parse_horse_block(block)

            if horse:
                horses.append(horse)

        races.append({
            "race": race,
            "horses": horses
        })

    return races


# -------------------------------------------------
# DEBUG TEST
# -------------------------------------------------

if __name__ == "__main__":

    with open("input\\input_word_new.txt", "r", encoding="utf-8") as f:

        raw_data = f.read()

    result = parse_input(raw_data)

    print(f"\nAntal lopp hittade: {len(result)}\n")

    for race_data in result:

        race = race_data["race"]
        horses = race_data["horses"]

        print("--------------------------------------------------")
        print(f"Avdelning: {race['race_no']}")
        print(f"Bana: {race['track']}")
        print(f"Distans: {race['distance']}")
        print(f"Starttyp: {race['start']}")
        print(f"Hästar hittade: {len(horses)}")
        print("--------------------------------------------------")

        for horse in horses:

            print(
                f"{horse['post']}. "
                f"{horse['horse']} | "
                f"Kusk: {horse['driver']} | "
                f"{horse['percent']}% | "
                f"{horse['equipment']} | "
                f"Rekord: {horse['record']} | "
                f"Historik: {len(horse['history'])}"
            )

        print()