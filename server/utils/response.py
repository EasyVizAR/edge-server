from quart import request


def maybe_wrap(result):
    """
    Wrap response in an envelope if requested.

    Otherwise, the response is not modified.
    """
    query = request.args

    if "envelope" in query:
        return { query.get("envelope"): result }
    else:
        return result
