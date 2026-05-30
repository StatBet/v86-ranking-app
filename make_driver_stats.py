import json

INPUT = r"C:\Users\Grinvald\Desktop\Ranking v85\Inklistrad text(12).txt"
OUTPUT = r"C:\Users\Grinvald\Desktop\Ranking v85\config\driver_stats.json"

driver_stats = {}

with open(INPUT, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:

    parts = line.strip().split("\t")

    if len(parts) < 11:
        continue

    if not parts[0].isdigit():
        continue

    try:
        name = parts[1].strip()

        starts = int(
            parts[4]
            .replace(" ", "")
            .replace("\xa0", "")
        )

        win_percent = float(
            parts[10]
            .replace("%", "")
            .replace(",", ".")
            .strip()
        )

        driver_stats[name] = {
            "starts": starts,
            "win_percent": win_percent
        }

    except:
        continue

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        driver_stats,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Klar! Skapade {len(driver_stats)} kuskar.")