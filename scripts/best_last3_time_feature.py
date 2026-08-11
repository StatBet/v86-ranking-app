import re

from scripts.speed_feature import normalize_time, parse_time_token, normalize_distance


def _extract_distance(distance_post):
    """Returnerar distansen frÃ¥n exempelvis '2140 : 4'."""
    if not distance_post:
        return None

    match = re.search(r"(\d+)", str(distance_post))
    if not match:
        return None

    return int(match.group(1))


def _get_best_normalized_time_last3(history, target_distance, target_auto):
    """BÃ¤sta normaliserade kilometertiden frÃ¥n hÃ¤stens tre senaste starter."""
    normalized_times = []
    target_distance = normalize_distance(target_distance)

    for start in history[:3]:
        time_token = start.get("time", "")
        parsed = parse_time_token(time_token)

        if not parsed:
            continue

        historical_distance = _extract_distance(
            start.get("distance_post", "")
        )

        if historical_distance is None:
            continue

        historical_distance = normalize_distance(historical_distance)

        normalized = normalize_time(
            historical_time=parsed["time"],
            historical_distance=historical_distance,
            historical_auto=parsed["auto"],
            historical_gallop=parsed["gallop"],
            target_distance=target_distance,
            target_auto=target_auto
        )

        if normalized is not None:
            normalized_times.append(float(normalized))

    if not normalized_times:
        return None

    return round(min(normalized_times), 2)


def calculate_best_last3_scores(
    horses,
    target_distance,
    target_auto,
    points,
    threshold=0.1
):
    """
    RÃ¤knar bÃ¤sta normaliserade tid frÃ¥n de tre senaste starterna.

    HÃ¤star grupperas med 0,1 sekund frÃ¥n gruppens snabbaste tid.
    Exempel: 12,1 och 12,2 fÃ¥r samma poÃ¤ng. 12,3 hamnar i nÃ¤sta grupp.

    Returnerar:
        score_map: {hÃ¤stnamn: poÃ¤ng}
        time_map: {hÃ¤stnamn: bÃ¤sta normaliserade tid}
    """
    valid = []
    time_map = {}

    for horse in horses:
        horse_name = horse.get("horse", "")
        best_time = _get_best_normalized_time_last3(
            history=horse.get("history", []),
            target_distance=target_distance,
            target_auto=target_auto
        )

        time_map[horse_name] = best_time

        if best_time is not None:
            valid.append({
                "horse": horse_name,
                "best_last3_time": best_time
            })

    valid.sort(key=lambda row: row["best_last3_time"])

    groups = []
    current_group = []
    current_group_start = None

    for row in valid:
        value = row["best_last3_time"]

        if not current_group:
            current_group = [row]
            current_group_start = value
            continue

        difference = round(value - current_group_start, 2)

        if difference <= threshold:
            current_group.append(row)
        else:
            groups.append(current_group)
            current_group = [row]
            current_group_start = value

    if current_group:
        groups.append(current_group)

    score_map = {}

    for group_index, group in enumerate(groups):
        score = points[group_index] if group_index < len(points) else 0

        for row in group:
            score_map[row["horse"]] = int(score)

    return score_map, time_map
