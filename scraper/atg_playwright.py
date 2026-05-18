import requests

url = "https://www.atg.se/services/racinginfo/v1/api/games/V85_2026-05-16_46_5"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.atg.se/"
}

response = requests.get(url, headers=headers)

print("STATUS:", response.status_code)
print("CONTENT TYPE:", response.headers.get("Content-Type"))

data = response.json()

print(data.keys())