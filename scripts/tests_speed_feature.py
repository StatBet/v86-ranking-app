from scripts.speed_feature import speed_score


# -------------------------------------------------
# MOCK DATA (5 LOPP)
# -------------------------------------------------

test_history = [
    {"time": "14,5a", "distance": 2140},
    {"time": "13,2a", "distance": 1640},
    {"time": "13,3a", "distance": 2100},
    {"time": "14,0a", "distance": 2600},
    {"time": "13,6a", "distance": 2100},
]


# -------------------------------------------------
# RUN TEST
# -------------------------------------------------

def main():

    print("🧪 TEST SPEED FEATURE START")

    score = speed_score(
        history=test_history,
        current_distance="2100",
        start_type="auto"
    )

    print("\n================ RESULT ================\n")
    print("SPEED SCORE:", score)

    if score > 0:
        print("\n✅ PASS: speed feature working")
    else:
        print("\n❌ FAIL: speed feature broken")


if __name__ == "__main__":
    main()