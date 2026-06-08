import re
import pandas as pd

df = pd.read_csv("ml_dataset.csv")

samples = df[
    (df["avg_odds"] == 0)
].head(20)

pattern = r"\n(\d+,\d+)\n\d+'"

print("=" * 80)
print("TEST AVG_ODDS REGEX")
print("=" * 80)

for _, row in samples.iterrows():

    raw = row["raw"]

    matches = re.findall(pattern, raw)

    print()
    print("=" * 80)
    print(row["date"], "Avd", row["race_no"], row["horse"])
    print("Nuvarande avg_odds:", row["avg_odds"])
    print("Regex-matches:", matches)
    print("-" * 80)

    lines = raw.splitlines()

    for i, line in enumerate(lines):
        if "," in line or "'" in line or line.strip() in ["--", "-"]:
            print(f"{i:03}: {line}")