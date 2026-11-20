"""Tests on small hand-made data: no API key, no network, no real outputs touched.

Run from the project root:  python -m pytest
Each test proves one promise the documents make (README, data_findings.md, improvement.md).
"""
import pandas as pd
import pytest

from pipeline.clean import apply_cleaning
from pipeline.compare_runs import compare
from pipeline.join import checked_left_join
from pipeline.load_ids import load_and_classify_ids


# ---------- hand-made data ----------
def films_table(revenues=(100, 200, 300, 400), collections=(10, 10, 10, None)):
    """Four films: three in one collection, one standalone, all released 2001 to 2004."""
    n = len(revenues)
    df = pd.DataFrame({
        "movie_id": pd.array(range(1, n + 1), dtype="int64"),
        "title": [f"Film {i}" for i in range(1, n + 1)],
        "release_date": pd.to_datetime([f"{2000 + i}-06-01" for i in range(1, n + 1)]),
        "budget": pd.array([10] * n, dtype="Int64"),
        "revenue": pd.array(list(revenues), dtype="Int64"),
        "collection_id": pd.array(list(collections), dtype="Int64"),
    })
    df["release_year"] = df["release_date"].dt.year.astype("Int64")
    return df


NO_FLAGS = pd.DataFrame({"check": pd.Series([], dtype="string"),
                         "movie_id": pd.Series([], dtype="Int64"), "value": pd.Series([], dtype="object")})


# ---------- 1. every candidate row is accounted for ----------
def test_every_row_is_accounted_for(tmp_path):
    """Stage 1: fetchable + quarantined = rows read. Stage 6: analysed + excluded = films in."""
    ids = tmp_path / "id_list.csv"
    ids.write_text("tmdb_id\n11\n12\n\nN/A\n-1\ntt0468569\n11\n12.5\n")
    fetchable, quarantine = load_and_classify_ids(ids)
    assert len(fetchable) + len(quarantine) == 8
    assert sorted(fetchable["movie_id"]) == [11, 12]

    flags = pd.DataFrame({"check": ["released_after_fetch"], "movie_id": pd.array([2], dtype="Int64"), "value": [None]})
    clean, excluded, _ = apply_cleaning(films_table(), flags)
    assert len(clean) + len(excluded) == 4
    assert excluded["reason"].tolist() == ["released_after_fetch"]


# ---------- 2. bad ids are classified, each with one reason ----------
def test_bad_ids_get_the_right_reason(tmp_path):
    ids = tmp_path / "id_list.csv"
    ids.write_text("tmdb_id\n11\n\nN/A\n-1\ntt0468569\n11\n12.5\n")
    _, quarantine = load_and_classify_ids(ids)
    reasons = dict(zip(quarantine["row_number"], quarantine["reason"]))
    # A decimal such as 12.5 gets its own reason and is quarantined, without crashing the load.
    assert reasons == {2: "blank", 3: "not_a_number", 4: "non_positive", 5: "imdb_format",
                       6: "repeat_of_earlier_row", 7: "not_whole_number"}
    assert quarantine.loc[quarantine["reason"].eq("repeat_of_earlier_row"), "repeat_of_row"].tolist() == [1]


# ---------- 3. the zero rule, both ways, and the empty case that once broke ----------
def test_zero_rule_and_zero_exclusions():
    films = films_table(revenues=(100, 0, 300, 400))
    clean, excluded, report = apply_cleaning(films, NO_FLAGS)
    assert len(excluded) == 0 and len(clean) == 4                 # no exclusions keeps every film
    assert clean.loc[clean["movie_id"].eq(2), "revenue"].isna().all()
    assert not clean.loc[clean["movie_id"].eq(2), "has_revenue"].any()
    assert report.set_index("rule").loc["zero_revenue_to_missing", "rows_affected"] == 1

    kept, _, report_off = apply_cleaning(films, NO_FLAGS, zero_as_missing=False)
    assert kept.loc[kept["movie_id"].eq(2), "revenue"].iloc[0] == 0
    assert report_off.set_index("rule").loc["zero_revenue_to_missing", "rows_affected"] == 0
    assert films["revenue"].iloc[1] == 0                         # the input table was not changed


# ---------- 4. the join refuses to duplicate a film ----------
def test_join_refuses_duplicates():
    films = films_table()
    report = {}
    one_lead = pd.DataFrame({"movie_id": pd.array([1, 2], dtype="int64"), "lead_name": ["A", "B"]})
    out = checked_left_join(films, one_lead, "lead", report)
    assert len(out) == len(films) and report == {"lead_matched": 2, "lead_no_match": 2}

    two_leads_for_film_1 = pd.DataFrame({"movie_id": pd.array([1, 1], dtype="int64"), "lead_name": ["A", "C"]})
    with pytest.raises(pd.errors.MergeError):
        checked_left_join(films, two_leads_for_film_1, "lead", {})


# ---------- 5. the change report names each kind of change ----------
def test_change_report_names_each_change():
    def result(verdict_2000, revenue_of_1, films_ids, standalones, list_print):
        summary = {"id_list_fingerprint": list_print, "rows_in_list": 10, "films_analysed": len(films_ids),
                   "fetched_from": "2026-11-19", "fetched_to": "2026-11-19",
                   "settings_fingerprint": "s", "code_fingerprint": "c"}
        films = pd.DataFrame({"movie_id": films_ids, "title": [f"Film {i}" for i in films_ids],
                              "revenue": [revenue_of_1 if i == 1 else 100.0 for i in films_ids],
                              "is_franchise": [True] * len(films_ids), "collection_name": ["X"] * len(films_ids)})
        tables = {"kpi_comparison": pd.DataFrame({"window": ["all_years", "from_2000"],
                                                  "verdict": ["franchise", verdict_2000],
                                                  "gap_ratio_medians": [3.0, 2.0]}),
                  "shortlist_franchise": pd.DataFrame({"collection_name": ["X", "Y"], "median_revenue": [200.0, 100.0]}),
                  "shortlist_standalone": pd.DataFrame({"title": standalones}),
                  "deal_note": pd.DataFrame({"window": ["all_years", "from_2000"], "collection_name": ["X", "X"],
                                             "demand_index": [2.5, 2.0]})}
        return summary, films, tables

    previous = result("franchise", 100.0, [1, 2, 3], ["Alpha", "Beta"], "list-a")
    current = result("no clear winner", 150.0, [1, 2], ["Alpha", "Gamma"], "list-b")
    report, flipped = compare(previous, current, "previous", "current")
    assert flipped
    assert "WARNING: the verdict changed in from_2000" in report
    assert "the candidate list changed" in report
    assert "Removed: 1 (Film 3)" in report
    assert "Box office revised by 1% or more: 1" in report
    assert "Standalone picks in: Gamma; out: Beta" in report

    same, flipped_same = compare(previous, previous, "previous", "previous")
    assert not flipped_same and "No change at all" in same