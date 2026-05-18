import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PARSER = BASE / "scripts" / "parse_word_structured.py"

EXPECTED_HORSES = 143


def run_parser():

    result = subprocess.run(
        [sys.executable, str(PARSER)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"   # 🔥 VIKTIG FIX
    )

    return result.stdout + "\n" + result.stderr


def extract_count(output: str):

    if not output:
        return None

    for line in output.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)

    return None


def main():

    print("🔒 RUNNING SYSTEM LOCK TEST\n")

    output = run_parser()

    print(output)

    count = extract_count(output)

    print("\n================ CHECK ================")

    if count != EXPECTED_HORSES:
        print(f"❌ FAIL: expected {EXPECTED_HORSES}, got {count}")
        sys.exit(1)

    print(f"✅ PASS: {count} horses OK")


if __name__ == "__main__":
    main()