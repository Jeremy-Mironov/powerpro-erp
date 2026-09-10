from powerpro.utils import guard_mirror


def guard(doc, method=None):
    guard_mirror(doc, flag="pp_is_mirror")
