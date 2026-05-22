import re


def clean_text(text):
    return (
        text.replace("\xa0", " ")
        .replace("", "")
        .replace("•", "")
        .strip()
    )


def is_race_header_line(line):
    return re.match(r"^Avdelning\s+\d+,?$", line.strip()) is not None


def parse_distance_post(line):
    line = clean_text(line)
    match = re.search(r"(\d+)\s*:\s*(\d+)", line)

    if not match:
        return 0, 0

    return int(match.group(1)), int(match.group(2))


def parse_percent(line):
    line = clean_text(line).replace("%", "")

    try:
        return int(line)
    except:
        return 0


def parse_money(line):
    line = clean_text(line).replace(" ", "")

    try:
        return int(line)
    except:
        return 0


def parse_horse_name(line):
    line = clean_text(line)
    line = re.sub(r"^\d+\s+", "", line)
    return line.strip()


def parse_number_and_name(line):
    line = clean_text(line)
    match = re.match(r"^(\d+)\s+(.+)$", line)

    if match:
        return int(match.group(1)), match.group(2).strip()

    return 0, line


def looks_like_horse_without_number(line):
    line = clean_text(line)

    if looks_like_date(line):
        return False

    if looks_like_distance_post(line):
        return False

    if looks_like_percent(line):
        return False

    if "Senaste 5" in line:
        return False

    if line in ["VIDEO", "Formrader", "Trend%:"]:
        return False

    return re.search(r"[a-zåäö]\d+$", line.lower()) is not None


def normalize_start_method(line):
    line = line.lower()

    if "auto" in line:
        return "auto"

    if "volt" in line:
        return "volt"

    return "unknown"


def looks_like_date(line):
    return re.match(r"^\d{4}-\d{2}-\d{2}$", clean_text(line)) is not None


def looks_like_distance_post(line):
    return re.search(r"\d+\s*:\s*\d+", clean_text(line)) is not None


def looks_like_percent(line):
    return re.match(r"^\d+%$", clean_text(line)) is not None


def looks_like_record(line):
    line = clean_text(line)
    return re.match(r"^(\d+\.)?\d{1,2},\d+[a-zA-ZÅÄÖåäö]*$", line) is not None


def is_simple_start_number(line):
    return re.match(r"^\d+$", clean_text(line)) is not None


def is_horse_line_with_number(line):
    line = clean_text(line)

    if looks_like_distance_post(line):
        return False

    if looks_like_date(line):
        return False

    return re.match(r"^\d+\s+[A-Za-zÅÄÖåäö].+", line) is not None


def parse_history(lines, start_index):
    history = []

    if start_index is None:
        return history

    i = start_index

    while i < len(lines):

        if is_race_header_line(lines[i]):
            break

        if is_simple_start_number(lines[i]) and i + 1 < len(lines):
            if is_horse_line_with_number(lines[i + 1]):
                break

        if is_horse_line_with_number(lines[i]):
            break

        if looks_like_horse_without_number(lines[i]):
            break

        if looks_like_date(lines[i]):
            date = lines[i]
            track = lines[i + 1] if i + 1 < len(lines) else ""
            driver = lines[i + 2] if i + 2 < len(lines) else ""
            placement = lines[i + 3] if i + 3 < len(lines) else ""
            dist_post = lines[i + 4] if i + 4 < len(lines) else ""
            time = lines[i + 5] if i + 5 < len(lines) else ""

            odds = ""
            prize = ""
            equipment = ""

            for j in range(i + 6, min(i + 15, len(lines))):
                value = lines[j]

                if re.match(r"^\d+,\d+$", value) or value.lower() == "ejsp":
                    odds = value

                elif "'" in value:
                    prize = value

                elif value in ["Vanlig", "Amerikansk", "-"]:
                    equipment = value
                    break

            raw = "\t".join([
                track,
                driver,
                placement,
                dist_post,
                time,
                odds,
                prize,
                equipment
            ])

            history.append({
                "raw": raw,
                "date": date,
                "track": track,
                "driver": driver,
                "placement": placement,
                "distance_post": dist_post,
                "time": time,
                "odds": odds,
                "equipment": equipment
            })

        i += 1

    return history


def parse_new_atg_format(raw_data):
    lines = [
        clean_text(line)
        for line in raw_data.splitlines()
        if clean_text(line)
    ]

    races = []
    i = 0

    while i < len(lines):

        if not is_race_header_line(lines[i]):
            i += 1
            continue

        race_no = int(re.search(r"\d+", lines[i]).group())

        track = "UNKNOWN"
        distance = 0
        start = "unknown"

        lookahead = lines[i:i + 25]

        for item in lookahead:
            if re.search(r"\d+\s*m", item):
                distance = int(re.search(r"(\d+)\s*m", item).group(1))

            if "auto" in item.lower() or "volt" in item.lower():
                start = normalize_start_method(item)

        for item in lookahead:
            lowered = item.lower()

            if (
                item != lines[i]
                and "trav" not in lowered
                and "auto" not in lowered
                and "volt" not in lowered
                and "bana" not in lowered
                and "lätt" not in lowered
                and not re.search(r"\d+\s*m", item)
                and not re.search(r"\d{1,2}:\d{2}", item)
            ):
                track = item
                break

        race = {
            "race_no": race_no,
            "track": track,
            "distance": distance,
            "start": start
        }

        horses = []
        i += 1

        while i < len(lines):

            if is_race_header_line(lines[i]):
                break

            # FORMAT 3:
            # spår
            # nummer + häst
            # kusk
            # spel%
            # rekord
            if (
                is_simple_start_number(lines[i])
                and i + 4 < len(lines)
                and is_horse_line_with_number(lines[i + 1])
                and looks_like_percent(lines[i + 3])
            ):
                post = int(lines[i])
                number, horse = parse_number_and_name(lines[i + 1])
                driver = lines[i + 2]
                percent = parse_percent(lines[i + 3])
                record = lines[i + 4]

                history_start = None

                for j in range(i, min(i + 20, len(lines))):
                    if "Senaste 5 starterna" in lines[j]:
                        history_start = j + 1
                        break

                history = parse_history(lines, history_start)

                raw = "\n".join([
                    horse,
                    f"{driver}\t{percent}%\t{race['distance']} : {post}\t0\t0%\t\t0-0-0\t\tVanlig\t{record}"
                ])

                horses.append({
                    "number": number,
                    "horse": horse,
                    "driver": driver,
                    "percent": percent,
                    "distance": race["distance"],
                    "post": post,
                    "prize_money": 0,
                    "trainer": "",
                    "equipment": "Vanlig",
                    "record": record,
                    "raw": raw,
                    "history": history
                })

                i += 1
                continue

            # FORMAT 4:
            # häst utan startnummer
            # Easter Eggv7
            # Jimmy H Andersson
            # 1%
            # 2640 : 1
            if (
                looks_like_horse_without_number(lines[i])
                and i + 5 < len(lines)
                and looks_like_percent(lines[i + 2])
                and looks_like_distance_post(lines[i + 3])
            ):
                horse = parse_horse_name(lines[i])
                driver = lines[i + 1]
                percent = parse_percent(lines[i + 2])

                horse_distance, post = parse_distance_post(lines[i + 3])
                prize_money = parse_money(lines[i + 4])

                trainer = ""
                equipment = "Vanlig"
                record = ""
                stats_line = "000-0-0"

                for j in range(i, min(i + 20, len(lines))):
                    if re.match(r"^\d{2,3}-\d+-\d+$", lines[j]):
                        stats_line = lines[j]

                    elif lines[j] in ["Vanlig", "Amerikansk", "-"]:
                        equipment = lines[j]

                    elif looks_like_record(lines[j]):
                        record = lines[j]

                history_start = None

                for j in range(i, min(i + 30, len(lines))):
                    if "Senaste 5 starterna" in lines[j]:
                        history_start = j + 1
                        break

                history = parse_history(lines, history_start)

                raw = "\n".join([
                    horse,
                    f"{driver}\t{percent}%\t"
                    f"{horse_distance} : {post}\t"
                    f"{prize_money}\t0%\t\t"
                    f"{stats_line}\t{trainer}\t"
                    f"{equipment}\t{record}"
                ])

                horses.append({
                    "number": len(horses) + 1,
                    "horse": horse,
                    "driver": driver.split("(")[0].strip(),
                    "percent": percent,
                    "distance": horse_distance,
                    "post": post,
                    "prize_money": prize_money,
                    "trainer": trainer,
                    "equipment": equipment,
                    "record": record,
                    "raw": raw,
                    "history": history
                })

                i += 1
                continue

            # FORMAT 2:
            # nummer + häst
            # kusk
            # spel%
            # distans : spår
            if (
                is_horse_line_with_number(lines[i])
                and i + 4 < len(lines)
                and looks_like_percent(lines[i + 2])
            ):
                number, horse = parse_number_and_name(lines[i])
                driver = lines[i + 1]
                percent = parse_percent(lines[i + 2])

                horse_distance = race["distance"]
                post = 0
                prize_money = 0
                equipment = "Vanlig"
                record = ""
                stats_line = "0-0-0"
                trainer = ""

                if looks_like_distance_post(lines[i + 3]):
                    horse_distance, post = parse_distance_post(lines[i + 3])
                    prize_money = parse_money(lines[i + 4]) if i + 4 < len(lines) else 0

                    for j in range(i, min(i + 20, len(lines))):
                        if re.match(r"^\d{2,3}-\d+-\d+$", lines[j]):
                            stats_line = lines[j]

                        elif lines[j] in ["Vanlig", "Amerikansk", "-"]:
                            equipment = lines[j]

                        elif looks_like_record(lines[j]):
                            record = lines[j]

                    trainer = lines[i + 8] if i + 8 < len(lines) else ""

                elif looks_like_record(lines[i + 3]):
                    record = lines[i + 3]

                history_start = None

                for j in range(i, min(i + 25, len(lines))):
                    if "Senaste 5 starterna" in lines[j]:
                        history_start = j + 1
                        break

                history = parse_history(lines, history_start)

                raw = "\n".join([
                    horse,
                    f"{driver}\t{percent}%\t{horse_distance} : {post}\t{prize_money}\t0%\t\t{stats_line}\t{trainer}\t{equipment}\t{record}"
                ])

                horses.append({
                    "number": number,
                    "horse": horse,
                    "driver": driver.split("(")[0].strip(),
                    "percent": percent,
                    "distance": horse_distance,
                    "post": post,
                    "prize_money": prize_money,
                    "trainer": trainer,
                    "equipment": equipment,
                    "record": record,
                    "raw": raw,
                    "history": history
                })

                i += 1
                continue

            i += 1

        races.append({
            "race": race,
            "horses": horses
        })

    return races