import os
import requests
import sys
import random


ITERATIONS = 100
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


created_photos = []


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


def upload_basic(headset, location_id, photo_path):
    item = {
        "camera_location_id": location_id
    }

    headers = {
        "Authorization": "Bearer " + headset['token']
    }

    req_url = "{}/photos".format(SERVER_URL)
    req = requests.post(req_url, headers=headers, json=item)
    photo = req.json()
    created_photos.append(photo['id'])

    headers = {
        "Authorization": "Bearer " + headset['token'],
        "Content-Type": "image/jpeg"
    }

    with open(file_path, "rb") as source:
        if photo['imageUrl'].startswith("http"):
            image_url = photo['imageUrl']
        else:
            image_url = SERVER_URL + photo['imageUrl']

        req = requests.put(image_url, data=source, headers=headers)


def upload_quick(headset, location_id, photo_path):
    headers = {
        "Authorization": "Bearer " + headset['token'],
        "Content-Type": "image/jpeg"
    }

    req_url = "{}/photos".format(SERVER_URL)
    with open(file_path, "rb") as source:
        req = requests.post(req_url, headers=headers, data=source)
        photo = req.json()
        created_photos.append(photo['id'])


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

    for i in range(ITERATIONS):
        upload_basic(headset, location_id, file_path)
        upload_quick(headset, location_id, file_path)
