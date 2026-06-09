from badge_rules import get_loppbadge

examples = [
    {"spread_1_8": 82, "gap_1_3": 20, "gap_1_4": 25},
    {"spread_1_8": 76, "gap_1_3": 20, "gap_1_4": 25},
    {"spread_1_8": 60, "gap_1_3": 20, "gap_1_4": 34},
    {"spread_1_8": 45, "gap_1_3": 18, "gap_1_4": 22},
]

for e in examples:
    badge = get_loppbadge(e)
    print(
        f"{badge['square']} {badge['label']} "
        f"- huvudgrupp rank 1-{badge['main_group']} "
        f"- {badge['hit_rate']}% "
        f"- {badge['reason']}"
    )