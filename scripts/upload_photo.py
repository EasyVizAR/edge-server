import os
import requests
import sys
import random

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")
ADD_FAKE_ANNOTATION = True
objects = ["object1", "object2","object3"]

def upload_item(file_path):
    item = {
        "contentType": "image/jpeg",
        "camera_location_id": "daa31ed1-d852-4c21-bef2-0536d3022652"
    }
     
    random_object = random.choice(objects)
    # Add a bounding box for an "object" for testing
    if ADD_FAKE_ANNOTATION:
        item['annotations'] = [{
            "boundary": {
                "height": 0.5,
                "width": 0.5,
                "top": 0.25,
                "left": 0.25
            },
            "confidence": 0.9,
            "label": random_object
        }]

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
