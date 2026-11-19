"""Stage 1: load the client's id list and classify every row."""
import numpy as np
import pandas as pd

import config


def load_and_classify_ids(path):
    """Read id_list.csv exactly as given and label every row.

    Takes:   path to id_list.csv
    Returns: (fetchable, quarantine) DataFrames
             fetchable  = unique, valid ids to request from the API
             quarantine = every other row, with a reason
    Asserts: rows read == fetchable + quarantine (nothing lost)
             fetchable ids are unique
    """
    # Read every row as text, exactly as the client sent it (Moodle 6)
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, skip_blank_lines=False)
    raw["row_number"] = np.arange(1, len(raw) + 1)   # row 1 = first id under the header

    value = raw[config.ID_COLUMN].str.strip()
    number = pd.to_numeric(value, errors="coerce")    # text that is not a number -> NaN

    # Label each row; the first matching rule wins
    raw["reason"] = np.select(
        [
            value.eq(""),                  # blank line
            value.str.fullmatch(r"tt\d+"), # IMDb-style id, not a TMDb id
            number.isna(),                 # e.g. "N/A"
            number <= 0,                   # e.g. -1
            number % 1 != 0,               # e.g. 12.5 (not a whole number)
        ],
        ["blank", "imdb_format", "not_a_number", "non_positive", "not_whole_number"],
        default="fetchable",
    )

    # Clean integer id, only for rows that passed the rules
    raw["movie_id"] = number.where(raw["reason"].eq("fetchable")).astype("Int64")

    # Repeats: keep the first row for each id, quarantine the later ones
    first_row = raw.groupby("movie_id")["row_number"].transform("min")
    is_repeat = raw["reason"].eq("fetchable") & raw["row_number"].ne(first_row)
    raw.loc[is_repeat, "reason"] = "repeat_of_earlier_row"
    raw["repeat_of_row"] = first_row.where(is_repeat).astype("Int64")

    fetchable = raw.loc[raw["reason"].eq("fetchable")].copy()
    quarantine = raw.loc[raw["reason"].ne("fetchable")].copy()

    # Nothing lost, nothing fetched twice
    assert len(fetchable) + len(quarantine) == len(raw), "rows lost during classification"
    assert fetchable["movie_id"].is_unique, "duplicate ids left in fetchable"
    assert fetchable["movie_id"].notna().all(), "fetchable row without an id"

    return fetchable, quarantine