# speed_ranking.py

def group_times(times, threshold=0.1):
    times = sorted(times)

    groups = []

    for t in times:
        placed = False

        for group in groups:
            if abs(t - group[0]) <= threshold:
                group.append(t)
                placed = True
                break

        if not placed:
            groups.append([t])

    return groups


def rank_groups(groups):
    scores = [24, 22, 20, 17, 15, 13, 10, 8]

    result = {}

    for i, group in enumerate(groups[:8]):
        for t in group:
            result[t] = scores[i]

    return result


def speed_score(times):
    groups = group_times(times)
    return rank_groups(groups)