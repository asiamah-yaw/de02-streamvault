"""Stage 4 - attach the lead actor and directors to films, and build talent tables.

Takes:   films (one row per film), cast, crew (stage 3), manifest (stage 2)
Returns: films_with_talent, film_directors, film_leads, director_job_counts, report
Asserts: films ids match the manifest; dtypes match before each join;
         each join is one-to-one and leaves the films row count unchanged.
"""
import pandas as pd

import config


def _pipe_join(values):
    """Join values into one text cell, e.g. [12, 87] -> '12|87'."""
    return "|".join(str(v) for v in values)


def build_leads(cast):
    """One lead per film for films; every candidate kept in film_leads."""
    cols = ["movie_id", "person_id", "name", "cast_order"]
    candidates = cast.loc[cast["cast_order"] <= config.LEAD_MAX_ORDER, cols]
    # Sort first so every 'keep first' below is deterministic.
    candidates = candidates.sort_values(["movie_id", "cast_order", "person_id"])
    before = len(candidates)
    film_leads = candidates.drop_duplicates(["movie_id", "person_id"]).reset_index(drop=True)
    lead_pair_duplicates = before - len(film_leads)

    lead = film_leads.drop_duplicates("movie_id")          # best billed, then lowest person_id
    other_candidates = film_leads.drop(index=lead.index)   # logged, not used on films
    lead = lead.rename(columns={"person_id": "lead_person_id", "name": "lead_name"})
    lead = lead.drop(columns="cast_order")
    return lead, film_leads, other_candidates, lead_pair_duplicates


def build_directors(crew):
    """film_directors (film x director) and a one-row-per-film summary."""
    rows = crew.loc[crew["job"].isin(config.DIRECTOR_JOBS), ["movie_id", "person_id", "name"]]
    before = len(rows)
    film_directors = (rows.drop_duplicates(["movie_id", "person_id"])
                          .sort_values(["movie_id", "person_id"])
                          .reset_index(drop=True))
    director_pair_duplicates = before - len(film_directors)

    summary = (film_directors.groupby("movie_id")
               .agg(director_ids=("person_id", _pipe_join),
                    director_names=("name", _pipe_join),
                    n_directors=("person_id", "size"))
               .reset_index())
    return summary, film_directors, director_pair_duplicates


def checked_left_join(left, right, name, report):
    """Left join on movie_id that proves it neither dropped nor duplicated a film."""
    assert left["movie_id"].dtype == right["movie_id"].dtype, (
        f"{name}: movie_id types differ ({left['movie_id'].dtype} vs {right['movie_id'].dtype})")
    rows_before = len(left)
    out = left.merge(right, on="movie_id", how="left",
                     validate="one_to_one", indicator=True)
    assert len(out) == rows_before, f"{name}: row count changed {rows_before} -> {len(out)}"
    merge_counts = out["_merge"].value_counts()
    report[f"{name}_matched"] = int(merge_counts.get("both", 0))
    report[f"{name}_no_match"] = int(merge_counts.get("left_only", 0))
    return out.drop(columns="_merge")


def join_talent(films, cast, crew, manifest):
    report = {"films_before": len(films)}

    # The films we built must be exactly the ids the API found (Phase 2).
    found = set(manifest.loc[manifest["status"].eq(200), "movie_id"].astype("int64"))
    assert set(films["movie_id"]) == found, "films ids do not match the fetch manifest"

    # Measured, never typed by hand.
    report["cast_credits_per_film"] = round(len(cast) / len(films), 1)
    report["crew_credits_per_film"] = round(len(crew) / len(films), 1)

    # Leads
    lead, film_leads, other_candidates, lead_dupes = build_leads(cast)
    has_cast = films["movie_id"].isin(cast["movie_id"])
    has_lead = films["movie_id"].isin(lead["movie_id"])
    report["lead_pair_duplicates_removed"] = lead_dupes
    report["films_no_cast_rows"] = int((~has_cast).sum())
    report["films_cast_but_no_lead"] = int((has_cast & ~has_lead).sum())
    report["films_2plus_lead_candidates"] = int(other_candidates["movie_id"].nunique())

    # Directors
    summary, film_directors, director_dupes = build_directors(crew)
    report["director_pair_duplicates_removed"] = director_dupes
    report["films_2plus_directors"] = int(summary["n_directors"].ge(2).sum())

    # Joins onto films: one row per film in, one row per film out.
    out = checked_left_join(films, lead, "lead", report)
    out = checked_left_join(out, summary, "directors", report)
    out["lead_person_id"] = out["lead_person_id"].astype("Int64")   # NaN made it float
    out["n_directors"] = out["n_directors"].fillna(0).astype("Int64")
    out[["director_ids", "director_names"]] = out[["director_ids", "director_names"]].fillna("")
    report["films_no_director"] = int(out["n_directors"].eq(0).sum())
    report["films_after"] = len(out)

    # How much evidence the talent question will have (threshold set in Phase 7).
    for label, table in [("directors", film_directors), ("leads", film_leads)]:
        films_per_person = table.groupby("person_id")["movie_id"].nunique()
        report[f"{label}_distinct_people"] = len(films_per_person)
        report[f"{label}_with_2plus_films"] = int(films_per_person.ge(2).sum())
        report[f"{label}_with_3plus_films"] = int(films_per_person.ge(3).sum())

    # Every Directing job, so Co-Director and similar show as their own lines.
    job_counts = (crew.loc[crew["department"].eq("Directing"), "job"]
                      .value_counts().rename_axis("job").reset_index(name="credits"))

    if len(other_candidates):
        print("  lead ties (not used on films):", other_candidates["movie_id"].tolist())
    return out, film_directors, film_leads, job_counts, report