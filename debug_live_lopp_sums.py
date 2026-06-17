def _num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def get_live_lopp_sum_debug(horses):
    total_sum = sum(_num(h.get("total_score", 0)) for h in horses)
    spike_sum = sum(_num(h.get("spike_score", 0)) for h in horses)

    return {
        "total_sum": round(total_sum, 1),
        "spike_sum": round(spike_sum, 1),
        "compact_total": total_sum <= 555,
        "compact_spike": spike_sum <= 810,
        "chaos_total": total_sum >= 750,
        "chaos_spike": spike_sum >= 1200,
    }