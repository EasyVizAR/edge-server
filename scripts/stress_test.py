"""
This script stress tests the server by creating a test headset and sending a
series of position updates and saving the echoed websocket updates from the
server.  It then reports the latency between the sent and received updates.
"""

import asyncio
import json
import os
import pprint
import time
import websockets

import requests


CALLS_PER_SECOND = 5
TEST_DURATION = 60


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")



def create_headset(location_id):
    url = "{}/headsets".format(SERVER_URL)
    data = {
        "name": "Stress Test",
        "type": "editor",
        "location_id": location_id
    }
    req = requests.post(url, json=data)
    headset = req.json()
    return headset


def get_headset(headset_id):
    url = "{}/headsets/{}".format(SERVER_URL, headset_id)
    req = requests.get(url)
    headset = req.json()
    return headset


def create_location():
    url = "{}/locations".format(SERVER_URL)
    data = {
        "name": "Stress Test",
    }
    req = requests.post(url, json=data)
    location = req.json()
    return location


def get_ws_url():
    url = "{}/ws".format(SERVER_URL)
    req = requests.get(url)
    return req.headers['location']


received_messages = []


async def receive_messages(ws):
    while True:
        msg = await ws.recv()

        ts = time.time()
        received_messages.append((ts, msg))



async def run_test(ws_url, headset):
    sleep_time = 1.0 / CALLS_PER_SECOND
    num_calls = TEST_DURATION * CALLS_PER_SECOND

    headers = {
        "Authorization": "Bearer " + headset['token']
    }

    last_cmd = None
    async with websockets.connect(ws_url, extra_headers=headers) as ws:
        await ws.send("subscribe headsets:updated /headsets/" + headset['id'])

        for i in range(num_calls):
            x = float(i) / num_calls
            y = time.time()
            cmd = "move {0} 0 0 {1} {2} 0 0".format(x, i, y)
            await ws.send(cmd)

            last_cmd = cmd

            try:
                await asyncio.wait_for(receive_messages(ws), timeout=sleep_time)
            except asyncio.TimeoutError:
                pass

        await ws.send("exit")

    print("Last command sent: " + last_cmd)


if __name__ == "__main__":
    ws_url = get_ws_url()
    print("Websocket URL: " + ws_url)

    location = create_location()
    print("Created location with ID " + location['id'])

    headset = create_headset(location['id'])
    print("Created headset with ID " + headset['id'])

    asyncio.run(run_test(ws_url, headset))

    headset = get_headset(headset['id'])
    print("State of the headset at the end of the test:")
    pprint.pprint(headset)

    print("Notifications that we received back from the server:")
    print("#, latency (seconds)")
    for recv_ts, msg in received_messages:
        data = json.loads(msg)

        progress = data['current']['position']['x']
        step = data['current']['orientation']['x']
        send_ts = data['current']['orientation']['y']

        delta = recv_ts - float(send_ts)

        print("{}, {}".format(step, delta))
