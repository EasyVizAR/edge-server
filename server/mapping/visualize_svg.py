import csv
import glob
import io
import json
import os

from time import time

import numpy as np
import svgwrite

from . import visualize_pointcloud as v
from .plyutil import read_ply_file


def initialize(object_files_path):
    data = {}

    for i, path in enumerate(glob.glob(object_files_path)):
        time_of_prev_mod = os.path.getmtime(path)
        mesh = read_ply_file(path)
        zplane = v.slice(mesh, 0, verticalz=False, json_serialize=True)
        data[path] = {"last_modified": time_of_prev_mod, "lines": zplane[1]}

    with open('data.json', 'w') as f:
        json.dump(data, f)
    print("Data, JSON file initialized")

    return data

def write_image(data, svg_destination_path):
    minx = maxx = minz = maxz = 0
    for path in data:
        for segment in data[path]['lines']:
            for point in segment:
                minx = min(point[0], minx)
                maxx = max(point[0], maxx)
                minz = min(point[2], minz)
                maxz = max(point[2], maxz)

    scale = 10
    # standard name = 'svgwrite-example.svg'
    dwg = svgwrite.Drawing(svg_destination_path, profile='tiny', size=(scale*(maxx-minx), scale*(maxz-minz)))
    for path in data:
        for line in data[path]["lines"]:
            p1f = ((line[0][0] - minx) * scale, (line[0][2] - minz) * scale)
            p2f = ((line[1][0] - minx) * scale, (line[1][2] - minz) * scale)
            dwg.add(dwg.line(start=p1f,
                             end=p2f,
                             stroke=svgwrite.rgb(0, 0, 255, '%')
                             )
                    )

    dwg.save()
    print("Svg saved")

def update(object_files_path):
    with open('data.json', 'r') as f:
        data = json.load(f)
    data_init_size = len(data)

    for i, path in enumerate(glob.glob(object_files_path)):
        time_of_prev_mod = os.path.getmtime(path)
        if path not in data or data[path]["last_modified"] < time_of_prev_mod:
            mesh = read_ply_file(path)
            zplane = v.slice(mesh, 0, verticalz=False, json_serialize=True)
            data[path] = {"last_modified": time_of_prev_mod, "lines": zplane[1]}

    if len(data) > data_init_size:
        with open('data.json', 'w') as f:
            json.dump(data, f)
            print("Data, JSON updated")
    else:
        print("JSON already up to date")

    return data

def update_lines(object_files_path, initialize = True):
    if initialize == True or not os.path.exists('data.json'):
        data = {}
        data_init_size = 0
    else:   # Update current line values
        with open('data.json', 'r') as f:
            data = json.load(f)
            data_init_size = len(data)

    for i, path in enumerate(glob.glob(object_files_path)):
        time_of_prev_mod = os.path.getmtime(path)
        update_lines_at_path = data == None or path not in data or data[path]["last_modified"] < time_of_prev_mod
        if initialize or update_lines_at_path:
            mesh = read_ply_file(path)
            zplane = v.slice(mesh, 0, verticalz=False, json_serialize=True)
            data[path] = {"last_modified": time_of_prev_mod, "lines": zplane[1]}

    if initialize or len(data) > data_init_size:
        with open('data.json', 'w') as f:
            json.dump(data, f)
        print("Data, JSON updated")
    else:
        print("JSON already up to date")

    return data

def main():
    planepoints = []
    pointgroups = []
    linegroups = []
    mtime = {}
    map_pcd_lines = {}

    data = None
    with open('data.json', 'r') as f:
        data = json.load(f)
    data_init_size = len(data)

    t1 = time()
    for i, path in enumerate(glob.glob("HoloLensData/seventhfloor/*.ply")):
        # If the path is not in size, we want to look at it and put it in size
        # If the path is in size and the current size is larger than the previous size, we want to look at it
        # If the path is in size and the current size is equal to the previous size, we don't want to look at it

        mt = os.path.getmtime(path)
        # if path not in mtime or mtime[path] < mt:
        if path not in data or data[path]["last_modified"] < mt:
            # mtime[path] = mt
            mesh = read_ply_file(path)
            zplane = v.slice(mesh, 0, verticalz=False, json_serialize=True)
            planepoints.extend(zplane[0])
            # pointgroups.append(zplane[0])
            # linegroups.append(zplane[2])
            # map_pcd_lines[path] = {"last_modified":mt, "lines":zplane[1]}
            map_pcd_lines[path] = {"last_modified": mt, "lines": zplane[1]}
            # linegroups.append(zplane[1])

            print(i)

    t2 = time()
    print(f"Slicing the mesh took {t2 - t1} seconds")

    t1 = time()
    if len(data) > data_init_size:
        with open('data.json', 'w') as f:
            json.dump(map_pcd_lines, f)
    t2 = time()
    print(f"Writing everything to JSON took {t2 - t1} seconds")

    data = None
    t1 = time()
    with open('data.json', 'r') as f:
        data = json.load(f)
    t2 = time()
    print(f"Reading everything from JSON took {t2 - t1} seconds")

    # print(type(data))
    t1 = time()
    lines = []
    for file in data:
        print(file)
        print(data[file])
        lines.extend(data[file]["lines"])
    t2 = time()
    print(f"Loading everything into array took {t2 - t1} seconds")

    """minx = min([x[0] for x in planepoints])
    maxx = max([x[0] for x in planepoints])
    minz = min([x[2] for x in planepoints])
    maxz = max([x[2] for x in planepoints])

    print([minx, maxx, minz, maxz])
    rangex = maxx - minx
    rangez = maxz - minz
    print([rangex, rangez])
    imgrange = 300
    range = max(rangex, rangez)

    scale = 1
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(rangex, rangez))
    for i, group in enumerate(linegroups):
        for j, line in enumerate(group):
            p1f = ((line[0][0] - minx) * scale, (line[0][2] - minz) * scale)
            p2f = ((line[1][0] - minx) * scale, (line[1][2] - minz) * scale)
            dwg.add(dwg.line(start=p1f,
                             end=p2f,
                             stroke='black',
                             stroke_width='0.1'
                             )
                    )

    #print(dwg.tostring())
    dwg.save()
    print("Svg saved")"""


def create_topdown_svg(surface_dir, output_path):
    data = update_lines(os.path.join(surface_dir, "*.ply"), initialize=False)
    write_image(data, output_path)


if __name__ == "__main__":
    #data = initialize()

    data = update_lines("HoloLensData/seventhfloor/*.ply", initialize=False)
    write_image(data, 'svgwrite-example.svg')
