import errno
import os
from json import JSONEncoder

import numpy as np


class GenericJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (list, tuple, set)):
            return super().default(o)
        else:
            return o.__dict__


async def save_image(file_path, image):
    print(f"Saving file to {file_path}")
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    await image.save(file_path)


def write_to_file(json, file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    file = open(file_path, 'w')
    file.write(json)
    file.close()


def append_to_file(line, file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    file = open(file_path, 'a')
    file.write(line)
    file.close()


def get_csv_line(params):
    return ",".join([str(p) for p in params]) + "\n"


def get_pixels(extrinsic, intrinsic, X):
    """
    Returns the x, y pixels for the given X vector
    :param extrinsic: extrinsic (4*4) matrix obtained from the headset
    :param intrinsic: intrinsic (3*3) matrix obtained from the headset
    :param X: the position vector
    :return: image pixels for the vector
    """
    intm = np.dot(extrinsic, np.append(X, 1))
    intm = (intm / intm[2])[:3]
    intm = np.dot(intrinsic, intm)[:2]
    return [intm[0], intm[1]]


def get_vector(extrinsic, intrinsic, Y):
    """
    Returns the original vector from the image pixels
    :param extrinsic: extrinsic (4*4) matrix obtained from the headset
    :param intrinsic: intrinsic (3*3) matrix obtained from the headset
    :param Y: the image pixels
    :return: original vector
    """
    intm = np.dot(np.linalg.inv(intrinsic), np.append(Y, 1))
    intm = intm * extrinsic[2][3]
    intm = np.append(intm, 1)
    return intm.tolist()
