import os
import requests
import sys


SERVER_URL = "http://localhost:5000"


def upload_item(file_path):
    item = {
        "contentType": "image/jpeg"
    }

    req_url = "{}/photos".format(SERVER_URL)
    req = requests.post(req_url, json=item)
    photo = req.json()

    headers = {
        "Content-Type": "image/jpeg"
    }

    with open(file_path, "rb") as source:
        if photo['imageUrl'].startswith("http"):
            image_url = photo['imageUrl']
        else:
            image_url = SERVER_URL + photo['imageUrl']

        req = requests.put(image_url, data=source, headers=headers)
        print("Response: {}".format(req.status_code))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <photo file path>".format(sys.argv[0]))
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print("File not found: {}".format(file_path))
        sys.exit(1)

    upload_item(file_path)
