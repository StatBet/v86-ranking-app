from pathlib import Path

file = Path("build_ml_dataset.py")
text = file.read_text(encoding="utf-8")

targets = [
    "def extract_avg_odds_raw",
    "def apply_raw_fallbacks",
    '"avg_odds"',
]

for target in targets:
    print("=" * 80)
    print(target)
    print("=" * 80)

    index = text.find(target)

    if index == -1:
        print("Hittades inte")
        continue

    start = max(0, index - 500)
    end = min(len(text), index + 1500)

    print(text[start:end])
    print()