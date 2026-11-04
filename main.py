
import os
import uuid
import requests

GOVEE_KEY = os.environ["GOVEE_API_KEY"]
RESULTS_URL = os.environ["ELECTION_JSON_URL"]

HEADERS = {
    "Govee-API-Key": GOVEE_KEY,
    "Content-Type": "application/json"
}

COLOURS = {
    "democrat": 255,
    "republican": 16711680,
    "purple": 8388736,
    "unknown": 16777215
}

def get_election_colour():
    import requests

    url = "https://thepeoplestally.com/data/results.json"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        results = response.json()

        races = results.get("races", {})

        if not isinstance(races, dict) or not races:
            return "unavailable"

        democrat_wins = 0
        republican_wins = 0

        for race in races.values():
            candidates = race.get("cands", [])

            if not isinstance(candidates, list):
                continue

            winner = None

            # First look for an explicitly marked winner.
            for candidate in candidates:
                if candidate.get("winner") is True:
                    winner = candidate
                    break

            # Otherwise, use the named winner if the race has been called.
            if winner is None and race.get("winner_name"):
                for candidate in candidates:
                    if candidate.get("name") == race["winner_name"]:
                        winner = candidate
                        break

            if winner is None:
                continue

            party = str(winner.get("party", "")).lower()

            if party in ("d", "democrat", "democratic", "democratic party"):
                democrat_wins += 1
            elif party in ("r", "republican", "republican party"):
                republican_wins += 1

        # 218 called wins are needed to secure House control.
        if democrat_wins >= 218:
            return "democrat"
        elif republican_wins >= 218:
            return "republican"
        elif democrat_wins + republican_wins > 0:
            return "purple"
        else:
            return "unavailable"

    except Exception as error:
        print(f"Election results error: {error}")
        return "unavailable"


def get_devices():
    response = requests.get(
        "https://openapi.api.govee.com/router/api/v1/user/devices",
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()
    return response.json()["data"]


def change_colour(device, colour):
    payload = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": device["sku"],
            "device": device["device"],
            "capability": {
                "type": "devices.capabilities.color_setting",
                "instance": "colorRgb",
                "value": COLOURS[colour]
            }
        }
    }

    response = requests.post(
        "https://openapi.api.govee.com/router/api/v1/device/control",
        headers=HEADERS,
        json=payload,
        timeout=20
    )
    response.raise_for_status()

    print(f"Updated {device['deviceName']} to {colour}")


def main():
    colour = get_election_colour()
    print(f"Congress control colour: {colour}")

    devices = get_devices()

    for device in devices:
        capabilities = device.get("capabilities", [])

        supports_rgb = any(
            capability.get("type") ==
            "devices.capabilities.color_setting"
            and capability.get("instance") == "colorRgb"
            for capability in capabilities
        )

        if supports_rgb:
            change_colour(device, colour)

    print("Finished updating compatible lights.")


if __name__ == "__main__":
    main()
