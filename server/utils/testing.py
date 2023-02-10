
def int_equal(a, b):
    """
    Test if two (possibly string) values are equal as integers.

    Example:

        int_equal(1, '1') is True
    """
    return int(a) == int(b)
