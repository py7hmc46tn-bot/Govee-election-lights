
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
    response = requests.get(RESULTS_URL, timeout=20)
    response.raise_for_status()
    results = response.json()

    house = results["house"]["control"].lower()
    senate = results["senate"]["control"].lower()

    valid = {"democrat", "republican"}

    if house not in valid or senate not in valid:
        return "unknown"

    if house == senate:
        return house

    return "purple"


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
