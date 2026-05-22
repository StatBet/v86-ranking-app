import re


def parse_results(raw_text):

    lines = [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]

    results = {}

    for i in range(len(lines)):

        line = lines[i]

        if line.isdigit():

            avd = line

            if i + 1 < len(lines):

                horse_line = lines[i + 1]

                match = re.match(
                    r"^\d+\s+(.+)$",
                    horse_line
                )

                if match:
                    horse_name = match.group(1).strip()

                    results[avd] = horse_name

    return results