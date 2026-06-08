from pathlib import Path

text = Path(
    "build_ml_dataset.py"
).read_text(
    encoding="utf-8"
)

targets = [
    "extract_avg_odds_raw",
    "avg_odds",
    "history",
    "raw"
]

for target in targets:

    idx = text.find(target)

    if idx == -1:
        continue

    print()
    print("=" * 80)
    print(target)
    print("=" * 80)

    start = max(0, idx - 1000)
    end = min(len(text), idx + 3000)

    print(text[start:end])