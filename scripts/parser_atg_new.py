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


def is_horse_name_line(line):
    return re.search(r"[shv]\d+$", line.strip()) is not None


def parse_horse_name_gender_age(line):
    line = clean_text(line)

    match = re.search(r"(.+?)([shv])(\d+)$", line)

    if not match:
        return line, "", 0

    return (
        match.group(1).strip(),
        match.group(2),
        int(match.group(3))
    )


def parse_percent(line):
    line = clean_text(line).replace("%", "")

    try:
        return int(line)
    except:
        return 0


def parse_distance_post(line):
    line = clean_text(line)

    match = re.search(r"(\d+)\s*:\s*(\d+)", line)

    if not match:
        return 0, 0

    return int(match.group(1)), int(match.group(2))


def parse_money(line):
    line = clean_text(line).replace(" ", "")

    try:
        return int(line)
    except:
        return 0


def parse_start_stats(line):
    line = clean_text(line)

    match = re.search(r"^(\d+)-(\d+)-(\d+)$", line)

    if not match:
        return ""

    return line


def normalize_start_method(line):
    line = line.lower()

    if "auto" in line:
        return "auto"

    if "volt" in line:
        return "volt"

    return "unknown"


def parse_track_from_history(line):
    line = clean_text(line)

    if "-" in line:
        return line.split("-")[0].strip()

    return line.strip()


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

        race_no_match = re.search(r"\d+", lines[i])
        race_no = int(race_no_match.group()) if race_no_match else 0

        track = "UNKNOWN"
        distance = 0
        start = "unknown"

        lookahead = lines[i:i + 20]

        for item in lookahead:
            if re.search(r"\d+\s*m", item):
                distance = int(re.search(r"(\d+)\s*m", item).group(1))

            if "autostart" in item.lower() or "voltstart" in item.lower():
                start = normalize_start_method(item)

        for item in lookahead:
            if item not in [
                lines[i],
                "Trav",
                "Autostart",
                "Voltstart"
            ] and not re.search(r"\d+\s*m", item) and "onsdag" not in item.lower():
                if item not in ["DISTANS & SPÅR"]:
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

            if not is_horse_name_line(lines[i]):
                i += 1
                continue

            horse_line = lines[i]
            horse_name, gender, age = parse_horse_name_gender_age(horse_line)

            driver = clean_text(lines[i + 1]) if i + 1 < len(lines) else ""
            percent = parse_percent(lines[i + 2]) if i + 2 < len(lines) else 0
            horse_distance, post = parse_distance_post(lines[i + 3]) if i + 3 < len(lines) else (0, 0)
            prize_money = parse_money(lines[i + 4]) if i + 4 < len(lines) else 0
            win_percent = parse_percent(lines[i + 5]) if i + 5 < len(lines) else 0

            stats_line = ""
            trainer = ""
            equipment = ""
            record = ""

            # leta efter statistik / tränare / vagn / rekord inom nästa 12 rader
            for j in range(i + 6, min(i + 18, len(lines))):
                if re.match(r"^\d+-\d+-\d+$", lines[j]):
                    stats_line = lines[j]
                    trainer = lines[j + 1] if j + 1 < len(lines) else ""
                    equipment = lines[j + 2] if j + 2 < len(lines) else ""
                    record = lines[j + 3] if j + 3 < len(lines) else ""
                    break

            history = []

            # hitta "Senaste 5 starterna"
            hist_start = None

            for j in range(i, min(i + 30, len(lines))):
                if "Senaste 5 starterna" in lines[j]:
                    hist_start = j + 1
                    break

            if hist_start:
                k = hist_start

                while k < len(lines):

                    if is_horse_name_line(lines[k]):
                        break

                    if is_race_header_line(lines[k]):
                        break

                    if re.match(r"^\d{4}-\d{2}-\d{2}$", lines[k]):
                        date = lines[k]
                        track_race = lines[k + 1] if k + 1 < len(lines) else ""
                        hist_driver = lines[k + 2] if k + 2 < len(lines) else ""
                        placement = lines[k + 3] if k + 3 < len(lines) else ""
                        dist_post = lines[k + 4] if k + 4 < len(lines) else ""
                        time = lines[k + 5] if k + 5 < len(lines) else ""

                        odds = ""
                        prize = ""
                        hist_equipment = ""

                        # odds/pris/vagn kan ligga med tomrader borttagna, så vi letar flexibelt
                        for m in range(k + 6, min(k + 14, len(lines))):
                            if re.match(r"^\d+,\d+$", lines[m]) or lines[m].lower() in ["ejsp", "ejsp."]:
                                odds = lines[m]
                            elif "'" in lines[m]:
                                prize = lines[m]
                            elif lines[m] in ["Vanlig", "Amerikansk"]:
                                hist_equipment = lines[m]
                                break

                        hist_track = parse_track_from_history(track_race)

                        raw_history = "\t".join([
                            hist_track,
                            hist_driver,
                            placement,
                            dist_post,
                            time,
                            odds,
                            prize,
                            hist_equipment
                        ])

                        history.append({
                            "raw": raw_history,
                            "date": date,
                            "track": hist_track,
                            "driver": hist_driver,
                            "placement": placement,
                            "distance_post": dist_post,
                            "time": time,
                            "odds": odds,
                            "equipment": hist_equipment
                        })

                        k += 8
                        continue

                    k += 1

            raw_horse = "\n".join([
                horse_line,
                f"{driver}\t{percent}%\t{horse_distance} : {post}\t{prize_money}\t{win_percent}%\t\t{stats_line}"
            ])

            horses.append({
                "horse": horse_name,
                "gender": gender,
                "age": age,
                "driver": driver.split("(")[0].strip(),
                "percent": percent,
                "distance": horse_distance,
                "post": post,
                "prize_money": prize_money,
                "win_percent_raw": win_percent,
                "trainer": trainer,
                "equipment": equipment,
                "record": record,
                "raw": raw_horse,
                "history": history
            })

            i += 1

        races.append({
            "race": race,
            "horses": horses
        })

    return races