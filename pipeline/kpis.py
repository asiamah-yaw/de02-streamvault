"""Stage 7: KPIs for both windows, shortlist and talent."""


def kpi_table(films):
    """Franchise vs standalone KPIs with a count beside every statistic.

    Takes:   cleaned films table (one window)
    Returns: one row per group (franchise / standalone)
    Asserts: both groups present (standalones not lost to null keys)
    """
    raise NotImplementedError("Stage 7 - built in Phase 7")


def both_windows(films):
    """Run kpi_table for all years and for the cutoff year onward.

    Takes:   cleaned films table
    Returns: dict of window name -> KPI table, plus whether the ranking flips
    Asserts: the 2000+ window is a subset of all years
    """
    raise NotImplementedError("Stage 7 - built in Phase 7")