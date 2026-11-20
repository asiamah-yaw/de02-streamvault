"""Stage 3: turn cached JSON into tables of a stated grain.

Reshape only: values are converted to proper types but not cleaned.
Problems such as zero budgets are left in place for stage 5 to diagnose.
"""
import json

import pandas as pd

import config


def read_cached(raw_dir, endpoint, movie_ids=None):
    """Load the saved 200 responses for one endpoint ("movie" or "credits").

    movie_ids: only these films (the current list); None reads every saved film.
    """
    files = sorted(raw_dir.glob(f"{endpoint}_*.json"))   # .404 files are skipped
    if movie_ids is not None:                            # older saved films are ignored, not analysed
        keep = {f"{endpoint}_{int(i)}.json" for i in movie_ids}
        files = [f for f in files if f.name in keep]
    return [json.loads(path.read_text(encoding="utf-8")) for path in files]


def require_columns(df, fields, table):
    """Stop loudly if a field we depend on is missing (fields declared in config)."""
    missing = [field for field in fields if field not in df.columns]
    if missing:
        raise KeyError(f"{table}: TMDb fields missing from the responses: {missing}")


def convert_types(films):
    """Parse dates and whole numbers; count every value the conversion blanked."""
    report = {}
    for col in config.DATE_FIELDS:
        text = films[col]
        blank = text.isna() | text.eq("")
        films[col] = pd.to_datetime(text.where(~blank), format="%Y-%m-%d", errors="coerce")
        report[f"{col}_blank"] = int(blank.sum())
        report[f"{col}_unparseable"] = int((films[col].isna() & ~blank).sum())
    for col in config.INT_FIELDS:
        before = films[col].isna()
        films[col] = pd.to_numeric(films[col], errors="coerce").astype("Int64")
        report[f"{col}_not_a_number"] = int((films[col].isna() & ~before).sum())
    films["release_year"] = films["release_date"].dt.year.astype("Int64")
    return films, report


def build_tables(raw_dir, movie_ids=None):
    """Flatten cached responses into three tables.

    Takes:   folder of cached JSON files; movie_ids = the films found for the current list
             (None reads every saved film, as the profiling notebook does)
    Returns: films  (one row per film)
             cast   (one row per film per cast credit)
             crew   (one row per film per crew credit = person x job)
             report (counts: rows, empty credits, values blanked by conversion)
    Asserts: films has one row per saved movie response
             movie_id unique in films; credit_id unique in cast and in crew
    """
    movies = read_cached(raw_dir, "movie", movie_ids)
    credits = read_cached(raw_dir, "credits", movie_ids)

    # films: one row per film (flat dicts first, then one DataFrame - Moodle 1)
    films = pd.DataFrame(movies)
    require_columns(films, [*config.FILM_FIELDS, config.COLLECTION_FIELD,
                            config.GENRES_FIELD], "movie")
    collection = films[config.COLLECTION_FIELD]
    films["collection_id"] = [c.get("id") if isinstance(c, dict) else None for c in collection]
    films["collection_name"] = [c.get("name") if isinstance(c, dict) else None for c in collection]
    films["genres"] = ["|".join(g["name"] for g in (gs or [])) for gs in films[config.GENRES_FIELD]]
    films = films[[*config.FILM_FIELDS, "collection_id", "collection_name", "genres"]]
    films = films.rename(columns=config.FILM_FIELDS)
    films["collection_id"] = films["collection_id"].astype("Int64")
    films, report = convert_types(films)

    # cast: one row per film per cast credit
    cast = pd.json_normalize(credits, record_path="cast", meta=["id"], meta_prefix="movie_")
    require_columns(cast, config.CAST_FIELDS, "cast")
    cast = cast[["movie_id", *config.CAST_FIELDS]].rename(columns=config.CAST_FIELDS)
    cast["movie_id"] = cast["movie_id"].astype("int64")      # same type as films, for joins

    # crew: one row per film per crew credit (one person can hold several jobs)
    crew = pd.json_normalize(credits, record_path="crew", meta=["id"], meta_prefix="movie_")
    require_columns(crew, config.CREW_FIELDS, "crew")
    crew = crew[["movie_id", *config.CREW_FIELDS]].rename(columns=config.CREW_FIELDS)
    crew["movie_id"] = crew["movie_id"].astype("int64")

    # Empty credits, counted two ways
    credit_ids = {c["id"] for c in credits}
    report["films"] = len(films)
    report["cast_rows"] = len(cast)
    report["crew_rows"] = len(crew)
    report["films_without_credits_file"] = int((~films["movie_id"].isin(credit_ids)).sum())
    report["films_with_empty_cast"] = sum(1 for c in credits if not c.get("cast"))
    report["films_with_empty_crew"] = sum(1 for c in credits if not c.get("crew"))

    # Nothing lost or duplicated in reshaping (counts computed, never typed)
    assert len(films) == len(movies), "films rows differ from saved movie files"
    assert films["movie_id"].is_unique, "duplicate movie_id in films"
    assert cast["credit_id"].is_unique, "duplicate credit_id in cast"
    assert crew["credit_id"].is_unique, "duplicate credit_id in crew"
    assert cast["movie_id"].isin(films["movie_id"]).all(), "cast row for an unknown film"
    assert crew["movie_id"].isin(films["movie_id"]).all(), "crew row for an unknown film"

    return films, cast, crew, report