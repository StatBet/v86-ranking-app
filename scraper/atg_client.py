import requests
from rankings.parser import rank_race


def get_v75():
    url = "https://www.atg.se/services/racinginfo/v1/api/games/V75"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.atg.se/"
    }

    response = requests.get(url, headers=headers)

    print("STATUS:", response.status_code)
    print("CONTENT TYPE:", response.headers.get("Content-Type"))

    if response.status_code != 200:
        return None

    return response.json()


data = get_v75()

if data:
    race = data["tracks"][0]["races"][0]

    ranking = rank_race(race)

    for r in ranking:
        print(r)