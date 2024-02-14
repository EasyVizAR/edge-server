import hashlib
import mimetypes
import os
import re
import tempfile

import magic

from quart import send_from_directory
from werkzeug import exceptions
from werkzeug.utils import secure_filename

import numpy as np
import PIL
from PIL import Image


# Module cairosvg does not work on Windows,
# check if it can be imported (will fail many tests otherwise)
cairosvg_imported = True
try:
    import cairosvg
except:
    cairosvg_imported = False


class FakeMagic:
    """
    A class that looks like libmagic but only guesses file type based on file
    extension. This servers as a fallback in case libmagic does not load
    correctly.
    """
    def from_file(self, path):
        mtype = mimetypes.guess_type(path)
        if mtype[0] is None:
            return "application/octet-stream"
        else:
            return mtype[0]


async def assemble_patches(patches, photo_path):
    rows = []
    cols = []
    current_row_id = None

    with tempfile.TemporaryDirectory() as tmpdir:
        for patch in patches:
            # Assume files name is of the format "{row #}_{col #}.jpg"
            # Then every time the row number changes, we merge the columns and
            # append to the list of rows.
            parts = patch.filename.split("_")
            if current_row_id is None:
                current_row_id = parts[0]
            if parts[0] != current_row_id:
                rows.append(np.hstack(cols))
                cols = []
                current_row_id = parts[0]

            filename = secure_filename(patch.filename)
            path = os.path.join(tmpdir, filename)
            await patch.save(path)

            cols.append(Image.open(path))

    if len(cols) > 0:
        rows.append(np.hstack(cols))

    combined = np.vstack(rows)
    combined = Image.fromarray(combined)

    final_path = photo_path + ".png"
    combined.save(final_path, format="png")

    return final_path


def get_magic_instance():
    # The magic library makes it easy to identify file types of uploaded files.
    # Annoyingly, we need to track down the location of the magic database when
    # installed as a snap.
    try:
        if "SNAP" in os.environ:
            magic_file = os.path.join(os.environ['SNAP'], "usr/lib/file/magic.mgc")
            return magic.Magic(magic_file=magic_file, mime=True)
        else:
            return magic.Magic(mime=True)
    except magic.MagicException as error:
        print("Error initializing magic object: {}".format(error))
        return FakeMagic()


def ext_from_type(ctype):
    return mimetypes.guess_extension(ctype)


def hash_file(path, block_size=2**20, method=hashlib.sha1):
    result = method()
    with open(path, "rb") as source:
        while True:
            data = source.read(block_size)
            if not data:
                break
            result.update(data)
    return result.hexdigest()


async def try_send_png(image_path, original_type, width=900):
    if original_type == "image/png":
        return await send_from_directory(os.path.dirname(image_path), os.path.basename(image_path))

    elif original_type == "image/svg+xml":
        if not cairosvg_imported:
            raise exceptions.NotFound("Unable to convert SVG to PNG, cairosvg module not imported")

        cache_dir = os.path.join(tempfile.gettempdir(), "cached_images")
        os.makedirs(cache_dir, exist_ok=True)

        # Compute hash of the original file, so we can cache the result of
        # converting the image but still work if the source image changes, e.g.
        # as generated map layers change.
        png_file = "{}-{}px.png".format(hash_file(image_path), width)
        png_path = os.path.join(cache_dir, png_file)

        if not os.path.exists(png_path):
            cairosvg.svg2png(url=image_path, write_to=png_path, output_width=width)

        return await send_from_directory(cache_dir, png_file)

    raise exceptions.BadRequest("Unable to satisfy image/png with file of type {}".format(original_type))


async def try_send_image(image_path, original_type, headers):
    accept = headers.get("Accept")

    # Deprecated in the HTTP standard, but useful if we need to specify output
    # file width.
    width = headers.get("Width")

    if accept is None:
        accepted_types = set(["*/*"])
    else:
        # Parsing the Accept header is actually fairly complicated with the
        # ability to specify priority levels.
        #
        # See: https://httpwg.org/specs/rfc7231.html#header.accept
        #
        # For our purposes, we can just treat it as a comma-separated list of
        # accepted MIME types and see if we can deliver any of them.
        accepted_types = set(re.split("[,;\s]+", accept))

    # Types satisfied by the original image
    satisfied_types = set(["*/*", "image/*", original_type])

    # Easy case: either the caller does not care what image type we return
    # or wants the same type as the existing file.
    if len(accepted_types & satisfied_types) > 0:
        return await send_from_directory(os.path.dirname(image_path), os.path.basename(image_path))

    # Convert SVG to PNG
    if original_type == "image/svg+xml" and "image/png" in accepted_types:
        try:
            width = int(width)
        except:
            width = 900

        return await try_send_png(image_path, original_type, width=width)

    raise exceptions.BadRequest("Unable to satisfy {} with file of type {}".format(accept, original_type))
