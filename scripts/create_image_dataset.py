import csv
import json
import os
import pprint
import shutil
import sys
import time

import numpy as np

import requests


SERVER=os.environ.get("SERVER", "http://localhost:5000")


def get_main_layer(location_id):
    url = f"{SERVER}/locations/{location_id}/layers"
    print(url)
    req = requests.get(url)
    layers = req.json()
    for layer in layers:
        if layer['type'] == "generated":
            return layer


def get_photo_list(location_id, device_id):
    url = f"{SERVER}/photos?location_id={location_id}&created_by={device_id}"
    print(url)
    req = requests.get(url)
    return req.json()


def download_photo(photo, photo_dir):
    photo_id = int(photo['id'])

    for fil in photo['files']:
        if fil['purpose'] == "photo":
            break

    url = "{}/photos/{}/{}".format(SERVER, photo_id, fil['name'])
    output_name = "{:08d}{}".format(photo_id, os.path.splitext(fil['name'])[1])
    output_path = os.path.join(photo_dir, output_name)

    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open(output_path, "wb") as output:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, output)

    return output_name


def download_map_images(location_id, layer, output_dir):
    url = "{}/locations/{}/layers/{}/image".format(SERVER, location_id, layer['id'])
    print(url)
    output_path = os.path.join(output_dir, "floorplan.svg")

    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open(output_path, "wb") as output:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, output)

    url = "{}/locations/{}/layers/{}/image.png".format(SERVER, location_id, layer['id'])
    output_path = os.path.join(output_dir, "floorplan.png")

    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open(output_path, "wb") as output:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, output)


def has_pose(photo):
    position = photo.get("camera_position")
    orientation = photo.get("camera_orientation")

    if position is None or orientation is None:
        return False

    fields = ["x", "y", "z"]
    position = np.array([position.get(k, 0) for k in fields])

    fields = ["x", "y", "z", "w"]
    orientation = np.array([orientation.get(k, 0) for k in fields])

    if np.allclose(position, 0) and np.allclose(orientation, 0):
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: {} <location-id> <device-id> <output-dir>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]
    device_id = sys.argv[2]
    output_dir = sys.argv[3]

    photo_dir = os.path.join(output_dir, "photos")
    os.makedirs(photo_dir, exist_ok=True)

    photos = get_photo_list(location_id, device_id)
    pprint.pprint(photos[0])

    layer = get_main_layer(location_id)
    download_map_images(location_id, layer, output_dir)

    camera_data = []
    for photo in photos:
        if not has_pose(photo):
            print("Photo {} is missing pose".format(photo['id']))
            continue

        filename = download_photo(photo, photo_dir)

        fields = [
            photo['id'],
            filename,
            photo['created']
        ]
        for k in ["x", "y", "z"]:
            fields.append(photo['camera_position'][k])
        for k in ["x", "y", "z", "w"]:
            fields.append(photo['camera_orientation'][k])
        camera_data.append(fields)

        # Prevent rate limiting at server
        time.sleep(0.2)

    column_names = ["id", "filename", "time", "position.x", "position.y", "position.z", "orientation.x", "orientation.y", "orientation.z", "orientation.w"]
    camera_path = os.path.join(output_dir, "camera.csv")
    with open(camera_path, "w") as output:
        writer = csv.writer(output)
        writer.writerow(column_names)
        writer.writerows(camera_data)
