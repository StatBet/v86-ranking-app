import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

HORSES_FILE = BASE / "output" / "horses.json"

with open(HORSES_FILE, "r", encoding="utf-8") as f:
    horses = json.load(f)

print("\n================ TEST DATA ================\n")

for i, h in enumerate(horses[:10], 1):
    print(f"{i}. {h.get('horse')} | form={h.get('form')} | driver={h.get('driver')}")