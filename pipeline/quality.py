"""Stage 5: profile the data and run quality checks."""


def profile(df):
    """Describe a table: shape, dtypes, nulls, numeric spread, top values.

    Takes:   any DataFrame
    Returns: profile table (one row per column)
    Asserts: nothing; this is for looking, not deciding
    """
    raise NotImplementedError("Stage 5 - built in Phase 5")


def quality_report(df):
    """Run named pass/fail checks (key unique, nulls in KPI columns, ranges).

    Takes:   films table
    Returns: report table (check, passed, detail)
    Asserts: nothing itself; the pipeline decides what a failure means
    """
    raise NotImplementedError("Stage 5 - built in Phase 5")