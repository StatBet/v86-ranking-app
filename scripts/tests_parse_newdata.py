import sys
from pathlib import Path
from io import StringIO
import contextlib

# -------------------------------------------------
# BASE PATH
# -------------------------------------------------

BASE = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE / "input" / "input_word_new.txt"

# -------------------------------------------------
# FIX: MAKE SURE WE CAN IMPORT SCRIPTS
# -------------------------------------------------

sys.path.append(str(BASE / "scripts"))

from parse_word_structured import main as parse_main


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def extract_count(output: str) -> int:
    for line in output.splitlines():
        if line.strip().isdigit():
            return int(line.strip())
    return 0


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    print("🔍 TEST NEW DATA START")
    print("INPUT FILE:", INPUT_FILE)
    print("EXISTS:", INPUT_FILE.exists())

    if not INPUT_FILE.exists():
        print("❌ INPUT FILE NOT FOUND")
        return

    buffer = StringIO()

    with contextlib.redirect_stdout(buffer):
        parse_main()

    output = buffer.getvalue()

    if not output:
        print("❌ NO OUTPUT FROM PARSER")
        return

    print("\n================ RAW PARSER OUTPUT ================\n")
    print(output)

    count = extract_count(output)

    print("\n================ CHECK ================\n")
    print("PARSED COUNT:", count)

    if count > 0:
        print(f"✅ PASS: {count} horses OK")
    else:
        print("❌ FAIL: 0 horses parsed")


# -------------------------------------------------
# RUN
# -------------------------------------------------

if __name__ == "__main__":
    main()