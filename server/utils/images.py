import hashlib
import os
import re
import tempfile

from quart import send_from_directory
from werkzeug import exceptions


# Module cairosvg does not work on Windows,
# check if it can be imported (will fail many tests otherwise)
cairosvg_imported = True
try:
    import cairosvg
except:
    cairosvg_imported = False


def ext_from_type(ctype):
    if ctype == "image/png":
        return ".png"
    elif ctype == "image/jpeg":
        return ".jpeg"
    elif ctype == "image/svg+xml":
        return ".svg"
    else:
        return ""


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
