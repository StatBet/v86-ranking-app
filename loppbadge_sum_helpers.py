def _num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def get_sum_loppbadge(horses):
    if not horses:
        return None

    total_sum = sum(_num(h.get("total_score", 0)) for h in horses)
    spike_sum = sum(_num(h.get("spike_score", 0)) for h in horses)

    if total_sum <= 1165 or spike_sum <= 1097:
        badge = "🟢 Kompakt lopp"
    elif total_sum >= 1538:
        badge = "🔥 Skrällopp"
    else:
        badge = None

    return {
        "badge": badge,
        "total_sum": round(total_sum, 1),
        "spike_sum": round(spike_sum, 1),
    }