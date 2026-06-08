import json

with open(
    "input_word_new.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

print(text[:10000])