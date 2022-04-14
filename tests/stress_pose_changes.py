"""
This code stress tests the headset pose change storage and retrieval.  It sends
a large number of headset pose changes and records time delay for processing
them.
"""

import datetime
import random
import time

import requests


stress_host = "http://halo05.wings.cs.wisc.edu:5000"
num_iterations = 3600
request_interval = 0.05


def create_headset():
    headset_name = datetime.datetime.now().strftime("Stress Test %Y-%m-%d %H:%M:%s")
    position = dict(x=0, y=0, z=0)
    response = requests.post(stress_host + "/headsets", json=dict(name=headset_name, position=position))
    return response.json()


def update_headset(headset):
    headset_url = stress_host + "/headsets/" + headset['id']

    start = time.time()
    response = requests.put(headset_url, json=headset)
    end = time.time()

    return response.status_code, end-start


def create_pose_change(headset):
    poses_url = stress_host + "/headsets/" + headset['id'] + "/pose-changes"

    orientation = dict(x=1, y=0, z=0)

    start = time.time()
    response = requests.post(poses_url, json=dict(position=headset['position'], orientation=orientation))
    end = time.time()

    return response.status_code, end-start


def get_headset(headset):
    headset_url = stress_host + "/headsets/" + headset['id']

    start = time.time()
    response = requests.get(headset_url)
    end = time.time()

    return response.status_code, end-start


def get_headset_poses(headset):
    poses_url = stress_host + "/headsets/" + headset['id'] + "/pose-changes"

    start = time.time()
    response = requests.get(poses_url)
    end = time.time()

    return response.status_code, end-start, response.headers['content-length']


def run_stress_test(headset):
    headset_url = stress_host + "/headsets/" + headset['id']

    errors = 0

    print("iteration, method, status_code, update_delay, get_delay, poses_delay, poses_size")
    for i in range(num_iterations):
        orientation = dict(x=1, y=0, z=0)
        for k in ['x', 'y', 'z']:
            headset['position'][k] = random.random()

        if i % 2 == 0:
            method = "put"
            status_code, update_delay = update_headset(headset)

        else:
            method = "post"
            status_code, update_delay = create_pose_change(headset)

        _, get_delay = get_headset(headset)
        _, poses_delay, poses_size = get_headset_poses(headset)

        print("{}, {}, {}, {}, {}, {}, {}".format(i, method, status_code, update_delay, get_delay, poses_delay, poses_size))

        time.sleep(request_interval)


if __name__ == "__main__":
    headset = create_headset()
    run_stress_test(headset)
