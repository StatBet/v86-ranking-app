import pandas as pd
from math import prod

DETAILS_FILE = "100k_new_signal_systems_540_details.csv"
TARGET_PROFILE = "balanced_540"
TARGET_DATE = 20251105

details = pd.read_csv(DETAILS_FILE)

case = details[
    (details["profile"] == TARGET_PROFILE)
    & (details["date"] == TARGET_DATE)
].copy()

if case.empty:
    raise ValueError("Hittar inte balanced_540 / 20251105 i 100k_new_signal_systems_540_details.csv")

print()
print("=" * 100)
print("BALANCED 540 - CASE 20251105")
print("=" * 100)

cols = [
    "race_no",
    "race_type",
    "wanted",
    "hit",
    "winner",
    "winner_rank",
    "winner_percent",
    "picked",
    "level1",
    "level2",
    "level3",
    "spik_red",
    "top3_sum",
    "round_rows",
    "round_hits",
]

print(case[cols].sort_values("race_no").to_string(index=False))

misses = case[case["hit"] == 0].copy()

print()
print("=" * 100)
print("MISSAR")
print("=" * 100)
print(misses[cols].to_string(index=False))

base_rows = int(case["round_rows"].iloc[0])

print()
print("=" * 100)
print("RADKALKYL FÖR ATT RÄDDA 8 RÄTT")
print("=" * 100)
print("Nuvarande rader:", base_rows)

rows = []

for _, miss in misses.iterrows():
    race_no = miss["race_no"]
    old_wanted = int(miss["wanted"])

    # Om vinnaren bara hade behövts läggas till:
    new_rows = int(base_rows / old_wanted * (old_wanted + 1))

    rows.append({
        "race_no": race_no,
        "race_type": miss["race_type"],
        "winner": miss["winner"],
        "winner_rank": miss["winner_rank"],
        "winner_percent": miss["winner_percent"],
        "old_wanted": old_wanted,
        "rows_if_add_winner": new_rows,
        "fits_540": int(new_rows <= 540),
        "picked_before": miss["picked"],
    })

rescue = pd.DataFrame(rows)

print(rescue.to_string(index=False))

case.to_csv("balanced_20251105_case_details.csv", index=False, encoding="utf-8-sig")
misses.to_csv("balanced_20251105_misses.csv", index=False, encoding="utf-8-sig")
rescue.to_csv("balanced_20251105_rescue_math.csv", index=False, encoding="utf-8-sig")

print()
print("Sparat:")
print("balanced_20251105_case_details.csv")
print("balanced_20251105_misses.csv")
print("balanced_20251105_rescue_math.csv")