"""Stage 6: apply cleaning decisions as flags, never silent drops."""


def apply_cleaning(films, zero_as_missing=True):
    """Add usability flags and derived columns according to the decisions.

    Takes:   films table; each decision is a parameter so it can be run both ways
    Returns: cleaned films table (same rows, extra flag columns)
    Asserts: row count unchanged (flags, not drops)
    """
    raise NotImplementedError("Stage 6 - built in Phase 6")