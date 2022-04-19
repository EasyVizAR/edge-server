import dataclasses

# Import to bring the marshmallow dataclass into this namespace so that
# other modules can import it. If we ever need to change the dataclass
# implementation across the project, this will make it easier.
from marshmallow_dataclass import dataclass


def field(description=None, **kwargs):
    """
    Wrap the native dataclasses.field to add a description.

    This makes it easier to add descriptions to dataclass fields and generate
    documentation.
    """
    if description is None:
        return dataclasses.field(**kwargs)
    else:
        # Yes, metadata nested in metadata seems redundant. That is another
        # reason this wrapper function exists.
        #
        # See: https://github.com/lovasoa/marshmallow_dataclass/issues/119
        metadata = {
            "metadata": {
                "description": description
            }
        }
        return dataclasses.field(metadata=metadata, **kwargs)
