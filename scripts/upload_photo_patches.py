import os
import requests
import sys
import random


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def create_headset(location_id, name="Stress Test Photo Uploader"):
    data = {
        "location_id": location_id,
        "name": name
    }
    url = "{}/headsets".format(SERVER_URL, json=data)
    req = requests.post(url, json=data)
    headset = req.json()
    print("Headset created with ID {}".format(headset['id']))
    return headset


def upload_patches(headset, location_id, photo_path):
    files = {
        "patches": (
            "00_00.jpg",
            open(photo_path, 'rb'),
            "image/jpeg"
        )
    }

    headers = {
        "Authorization": "Bearer " + headset['token']
    }

    req_url = "{}/photos".format(SERVER_URL)
    with open(file_path, "rb") as source:
        req = requests.post(req_url, headers=headers, files=files)
        photo = req.json()
        print(photo)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {} <location id> <photo file path>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]
    file_path = sys.argv[2]

    if not os.path.exists(file_path):
        print("File not found: {}".format(file_path))
        sys.exit(1)

    headset = create_headset(location_id)
    upload_patches(headset, location_id, file_path)

