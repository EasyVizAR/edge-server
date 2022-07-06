def patch_by_path(obj, path_components, value):
    current = obj
    for pc in path_components[:-1]:
        if isinstance(current, dict):
            current = current[pc]
        else:
            current = getattr(current, pc)

    if isinstance(current, dict):
        current[path_components[-1]] = value
    else:
        setattr(current, path_components[-1], value)


def patch_object(obj, changes):
    """
    Patch an object from a dictionary of changes.

    This is slightly more flexible than Python's built-in dictionary update in
    that it allows selectively changing specific fields in nested dictionaries.

    In the following example, we have a headset object, which contains a
    position dictionary. The patch_object call updates the headset object by
    only changing the "y" field and nothing else.

    Example:

        headset.position = {
            "x": 0,
            "y": 0,
            "z": 0
        }

        patch_object(headset, {"position.y": 1})
    """
    for key, value in changes.items():
        components = key.split(".")
        if len(components) == 1:
            setattr(obj, key, value)
        else:
            patch_by_path(obj, components, value)
