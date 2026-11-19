"""Stage 5 - profile the films as TMDb gave them. Detects and counts; changes nothing.

Takes:   films (stage 3), manifest (stage 2), quarantine (stage 1)
Returns: report (one row per check), flags (one row per check x film), skew (group x window)
Never stops the run on a data problem: everything is reported for stage 6 to decide.
"""
import numpy as np
import pandas as pd

import config


def _missing(money):
    """Missing = null or <= 0 (a 0 on TMDb usually means 'not entered')."""
    return money.isna() | money.fillna(0).le(0)


def _windows(films):
    """The brief's two windows. The cutoff year is inclusive."""
    return {"all_years": films,
            f"from_{config.WINDOW_CUTOFF_YEAR}": films[films["release_year"].ge(config.WINDOW_CUTOFF_YEAR).fillna(False)]}


def quality_report(films, manifest, quarantine):
    rows, flag_frames = [], []

    def add(check, count, denominator=None, group="all", window="all", note=""):
        rows.append({"check": check, "group": group, "window": window,
                     "count": count, "denominator": denominator, "note": note})

    def flag(check, ids, values=None):
        flag_frames.append(pd.DataFrame({"check": check, "movie_id": list(ids),
                                         "value": list(values) if values is not None else None}))

    # Split by the raw field, not the franchise label (still an assumption).
    films = films.assign(group=np.where(films["collection_id"].notna(), "in_collection", "no_collection"),
                         budget_missing=_missing(films["budget"]),
                         revenue_missing=_missing(films["revenue"]))

    # 1. Budget / revenue combinations, per group and window
    combos = {"both_present": ~films["budget_missing"] & ~films["revenue_missing"],
              "budget_missing_only": films["budget_missing"] & ~films["revenue_missing"],
              "revenue_missing_only": ~films["budget_missing"] & films["revenue_missing"],
              "both_missing": films["budget_missing"] & films["revenue_missing"]}
    for window, w in _windows(films).items():
        for group, g in w.groupby("group"):
            for name, mask in combos.items():
                add(f"money_{name}", int(mask.loc[g.index].sum()), len(g), group, window)
    flag("budget_missing", films.loc[films["budget_missing"], "movie_id"])
    flag("revenue_missing", films.loc[films["revenue_missing"], "movie_id"])

    # 2. Skew, on films with usable revenue
    usable = films[~films["revenue_missing"]]
    skew_rows = []
    for window, w in _windows(usable).items():
        for group, g in w.groupby("group"):
            rev = g["revenue"].astype("float64")
            skew_rows.append({"group": group, "window": window, "n": len(g),
                              "mean": rev.mean(), "median": rev.median(), "max": rev.max(),
                              "top_film_share": rev.max() / rev.sum(),
                              "top_film_id": int(g.loc[rev.idxmax(), "movie_id"])})
    skew = pd.DataFrame(skew_rows)

    # 3. Group sizes and collections
    for window, w in _windows(films).items():
        for group, g in w.groupby("group"):
            add("films", len(g), group=group, window=window)
            add("films_usable_revenue", int((~g["revenue_missing"]).sum()), len(g), group, window)
    per_collection = films["collection_id"].dropna().value_counts()
    add("collections", len(per_collection))
    add("collections_with_one_film_in_list", int(per_collection.eq(1).sum()), len(per_collection))

    # 4. Lowest non-zero values and extreme ratios (thresholds are read from these)
    for field in ["budget", "revenue"]:
        low = films.loc[~films[f"{field}_missing"]].nsmallest(10, field)
        flag(f"lowest_{field}", low["movie_id"], low[field])
    both = films[combos["both_present"]].assign(
        ratio=lambda d: d["revenue"].astype("float64") / d["budget"].astype("float64"))
    flag("highest_revenue_budget_ratio", both.nlargest(5, "ratio")["movie_id"], both.nlargest(5, "ratio")["ratio"].round(2))
    flag("lowest_revenue_budget_ratio", both.nsmallest(5, "ratio")["movie_id"], both.nsmallest(5, "ratio")["ratio"].round(2))

    # 5. Status
    for status, n in films["status"].value_counts(dropna=False).items():
        add("status", int(n), len(films), group=str(status))
    unknown = ~films["status"].isin(config.KNOWN_STATUSES)
    add("status_unknown_value", int(unknown.sum()), len(films))
    flag("status_not_released", films.loc[films["status"].ne("Released"), "movie_id"], films.loc[films["status"].ne("Released"), "status"])

    # 6. Release dates - compared with when the data was fetched, never with today
    stamps = manifest["fetched_at"]
    if pd.api.types.is_numeric_dtype(stamps):                 # seconds since 1970
        fetched = pd.to_datetime(stamps, unit="s", errors="coerce", utc=True).max()
    else:                                                     # text timestamps
        fetched = pd.to_datetime(stamps, errors="coerce", utc=True).max()
    fetched = fetched.tz_convert(None)
    after = films["release_date"].gt(fetched).fillna(False)
    add("release_year_min", int(films["release_year"].min()))
    add("release_year_max", int(films["release_year"].max()))
    add("released_after_fetch", int(after.sum()), len(films), note=f"fetched up to {fetched:%Y-%m-%d}")
    flag("released_after_fetch", films.loc[after, "movie_id"])
    add("films_before_cutoff", int(films["release_year"].lt(config.WINDOW_CUTOFF_YEAR).sum()), len(films),
        note=f"cutoff {config.WINDOW_CUTOFF_YEAR} is inclusive (>=)")

    # 7. Possible duplicates the id list cannot show
    imdb = films["imdb_id"].fillna("").str.strip()
    add("imdb_id_blank", int(imdb.eq("").sum()), len(films))
    dup_imdb = imdb.ne("") & imdb.duplicated(keep=False)
    add("imdb_id_repeated", int(dup_imdb.sum()), len(films))
    flag("imdb_id_repeated", films.loc[dup_imdb, "movie_id"], imdb[dup_imdb])
    title_key = (films["title"].fillna("").str.casefold().str.strip().str.replace(r"\s+", " ", regex=True)
                 + "|" + films["release_year"].astype("string").fillna(""))
    dup_title = title_key.duplicated(keep=False)
    add("title_year_repeated", int(dup_title.sum()), len(films))
    flag("title_year_repeated", films.loc[dup_title, "movie_id"], films.loc[dup_title, "title"])
    imdb_rows = quarantine[quarantine["reason"].eq("imdb_format")]
    for _, q in imdb_rows.iterrows():          # a handful of quarantined rows, not the films table
        value = q[config.ID_COLUMN].strip()
        match = films.loc[imdb.eq(value), "movie_id"]
        add("quarantined_imdb_id_found_in_films", len(match), note=f"row {q['row_number']} {value}")
        flag("quarantined_imdb_id_found_in_films", match, [value] * len(match))

    # 8. Possible sequels with no collection - a review list, not a measurement
    no_coll = films[films["group"].eq("no_collection")]
    looks_sequel = no_coll["title"].fillna("").str.contains(config.SEQUEL_PATTERN, regex=True)
    add("no_collection_title_looks_like_sequel", int(looks_sequel.sum()), len(no_coll), note="review list; precision unknown")
    flag("no_collection_title_looks_like_sequel", no_coll.loc[looks_sequel, "movie_id"], no_coll.loc[looks_sequel, "title"])

    # 9. Low value checks, one line each
    add("vote_count_below_threshold", int(films["vote_count"].lt(config.LOW_VOTE_COUNT).sum()), len(films),
        note=f"threshold {config.LOW_VOTE_COUNT}")
    add("runtime_missing_or_zero", int(_missing(films["runtime"]).sum()), len(films))

    report = pd.DataFrame(rows).astype({"count": "Int64", "denominator": "Int64"})
    flags = pd.concat([f for f in flag_frames if len(f)], ignore_index=True)
    flags["movie_id"] = flags["movie_id"].astype("Int64")
    return report, flags, skew