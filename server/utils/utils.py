import errno
import os
from json import JSONEncoder


class GenericJsonEncoder(JSONEncoder):
    def default(self, o):
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
