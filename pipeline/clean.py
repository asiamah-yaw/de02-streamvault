"""Stage 6 - turn films_talent into the analysis table. Every rule's effect is counted.

Takes:   films_talent (stage 4), quality_flags (stage 5)
Returns: films_clean, excluded (with reason), report (one row per rule)
Order:   exclusions -> zero rule -> franchise label -> window -> collection counts and positions
Asserts: clean + excluded == input rows; movie_id unique; the input table is not changed.
"""
import numpy as np
import pandas as pd

import config


def apply_cleaning(films, quality_flags, zero_as_missing=True, overrides=None):
    overrides = config.FRANCHISE_OVERRIDES if overrides is None else overrides
    rows_in = len(films)
    df = films.copy()                                  # never modify the caller's table
    report = []

    def add(rule, rows_affected, note=""):
        report.append({"rule": rule, "rows_affected": rows_affected, "note": note})

    # 1. Exclusions, decided from stage 5 flags (no string parsing)
    hits = quality_flags.loc[quality_flags["check"].isin(config.EXCLUDE_CHECKS), ["movie_id", "check"]]
    reasons = hits.groupby("movie_id")["check"].agg("|".join)
    is_excluded = df["movie_id"].isin(reasons.index)
    excluded = df.loc[is_excluded].copy()
    excluded["reason"] = excluded["movie_id"].map(reasons)   # map on the excluded rows only
    df = df.loc[~is_excluded].copy()
    add("exclude_not_released_or_future", int(is_excluded.sum()), "insurance; checks: " + ", ".join(config.EXCLUDE_CHECKS))

    # 2. Zero rule: budget or revenue <= 0 means 'not entered' (insurance for next year's list)
    for field in ["budget", "revenue"]:
        zero = df[field].le(0).fillna(False) if zero_as_missing else pd.Series(False, index=df.index)
        df.loc[zero, field] = pd.NA
        df[f"has_{field}"] = df[field].notna()
        add(f"zero_{field}_to_missing", int(zero.sum()), "insurance; proven by a test with a made-up zero row")

    # 3. Franchise label (decision: in a TMDb collection; ADR)
    df["is_franchise"] = df["collection_id"].notna()
    forced = df["movie_id"].isin(list(overrides))
    df.loc[forced, "is_franchise"] = True              # an overridden film keeps a null collection
    not_found = sorted(set(overrides) - set(df["movie_id"]))
    add("franchise_overrides_applied", int(forced.sum()), f"ids not in list: {not_found}" if not_found else "")

    # 4. Window: nullable, so a missing year is not silently 'before 2000'
    df["from_2000"] = df["release_year"].ge(config.WINDOW_CUTOFF_YEAR).astype("boolean")
    add("from_2000_missing_year", int(df["from_2000"].isna().sum()), f"cutoff {config.WINDOW_CUTOFF_YEAR} inclusive (>=)")
    for window, mask in [("all_years", pd.Series(True, index=df.index)), ("from_2000", df["from_2000"].fillna(False))]:
        add(f"franchise_films_{window}", int((df["is_franchise"] & mask).sum()))
        add(f"standalone_films_{window}", int((~df["is_franchise"] & mask).sum()))

    # 5. Position among the LISTED films of each collection (not the position in the series)
    members = df.loc[df["collection_id"].notna()].sort_values(["collection_id", "release_date", "movie_id"])
    size = members.groupby("collection_id")["movie_id"].transform("size")
    rank = members.groupby("collection_id").cumcount() + 1
    position = np.select([size.eq(1), rank.eq(1), rank.eq(size)], ["only_listed", "first", "last"], default="middle")
    df["films_in_collection_list"] = pd.Series(0, index=df.index, dtype="Int64")
    df.loc[members.index, "films_in_collection_list"] = size
    df["entry_rank"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[members.index, "entry_rank"] = rank
    df["entry_position"] = "standalone"
    df.loc[members.index, "entry_position"] = position
    for label, n in df["entry_position"].value_counts().items():
        add(f"entry_position_{label}", int(n))
    middle = df["entry_position"].eq("middle")
    add("collections_with_a_middle_film", int(df.loc[middle, "collection_id"].nunique()), "needs 3+ listed films")

    assert len(df) + len(excluded) == rows_in, "a film was lost or counted twice in cleaning"
    assert df["movie_id"].is_unique, "movie_id repeated after cleaning"
    return df.reset_index(drop=True), excluded, pd.DataFrame(report)