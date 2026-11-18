"""Stage 9: compare pipeline output against the live API."""


def spot_check(films, sample_ids):
    """Re-fetch chosen ids live and compare field by field.

    Takes:   cleaned films table; ids chosen by the four slices
    Returns: spot-check table (id, field, ours, api, diff, class, action)
    Asserts: tolerance is set before comparing
    """
    raise NotImplementedError("Stage 9 - built in Phase 9")