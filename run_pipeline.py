"""Run the StreamVault pipeline end to end.

Usage:  python run_pipeline.py
Needs:  the TMDB_API_KEY environment variable (see README).
"""
import os
import sys

import pandas as pd


import config
from pipeline.clean import apply_cleaning
from pipeline.fetch import fetch_all
from pipeline.flatten import build_tables
from pipeline.join import join_talent
from pipeline.kpis import both_windows
from pipeline.load_ids import load_and_classify_ids
from pipeline.quality import quality_report
from pipeline.spotcheck import spot_check


def check_api_key():
    """Stop at once, with a clear message, if the API key is missing."""
    if not os.environ.get(config.API_KEY_ENV_VAR):
        sys.exit(f"{config.API_KEY_ENV_VAR} is not set. See README, step 4.")


def heading(title):
    """Print an ETL section heading so the run shows where it is."""
    print(f"\n== {title} ==")


def main():
    check_api_key()
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    heading("EXTRACT")
    fetchable, quarantine = load_and_classify_ids(config.ID_LIST_PATH)  # stage 1
    classified = pd.concat([fetchable, quarantine]).sort_values("row_number")
    classified.to_csv(config.OUTPUT_DIR / "ids_classified.csv", index=False)
    quarantine.to_csv(config.OUTPUT_DIR / "quarantine.csv", index=False)
    print(f"[1 load] {len(classified)} rows read | {len(fetchable)} fetchable "
          f"| {len(quarantine)} quarantined -> outputs/quarantine.csv")
    manifest = fetch_all(fetchable["movie_id"].tolist())                # stage 2
    manifest.to_csv(config.OUTPUT_DIR / "fetch_manifest.csv", index=False)
    movies = manifest.loc[manifest["endpoint"].eq("movie")]
    live_calls = (manifest["status"].notna() & ~manifest["from_cache"]).sum()
    not_found = movies.loc[movies["status"].eq(404), "movie_id"].tolist()
    print(f"[2 fetch] {len(movies)} ids | {movies['status'].eq(200).sum()} found "
          f"| {len(not_found)} not found | {live_calls} live calls "
          f"-> outputs/fetch_manifest.csv")
    if not_found:
        print(f"          not found on TMDb: {not_found}")
    heading("VALIDATE")
    films, cast, crew, flat_report = build_tables(config.RAW_DIR)       # stage 3
    for name, table in {"films": films, "cast": cast, "crew": crew}.items():
        table.to_csv(config.OUTPUT_DIR / f"{name}.csv", index=False)
    pd.Series(flat_report).to_csv(config.OUTPUT_DIR / "flatten_report.csv", header=["count"])
    print(f"[3 flatten] films {len(films)} | cast {len(cast)} | crew {len(crew)} rows "
          f"-> outputs/films.csv, cast.csv, crew.csv")
    print(f"            empty cast {flat_report['films_with_empty_cast']} "
          f"| empty crew {flat_report['films_with_empty_crew']} "
          f"| no credits file {flat_report['films_without_credits_file']} "
          f"| release_date blank {flat_report['release_date_blank']}, "
          f"unparseable {flat_report['release_date_unparseable']}")
    # Stage 5 - profile films as TMDb gave them (reports, never fixes)
    quality, quality_flags, quality_skew = quality_report(films, manifest, quarantine)
    quality.to_csv(config.OUTPUT_DIR / "quality_report.csv", index=False)
    quality_flags.to_csv(config.OUTPUT_DIR / "quality_flags.csv", index=False)
    quality_skew.to_csv(config.OUTPUT_DIR / "quality_skew.csv", index=False)
    print(f"[5 quality] {len(quality)} checks | {quality_flags['movie_id'].nunique()} films flagged "
          "-> outputs/quality_report.csv, quality_flags.csv, quality_skew.csv")

    heading("TRANSFORM")
        # Stage 4 - join lead actor and directors onto films
    films_talent, film_directors, film_leads, job_counts, join_report = join_talent(
        films, cast, crew, manifest)
    films_talent.to_csv(config.OUTPUT_DIR / "films_with_talent.csv", index=False)
    film_directors.to_csv(config.OUTPUT_DIR / "film_directors.csv", index=False)
    film_leads.to_csv(config.OUTPUT_DIR / "film_leads.csv", index=False)
    job_counts.to_csv(config.OUTPUT_DIR / "director_job_counts.csv", index=False)
    (pd.Series(join_report, name="value").rename_axis("measure").reset_index()
       .to_csv(config.OUTPUT_DIR / "join_report.csv", index=False))
    print(f"[4 join] films {join_report['films_before']} -> {join_report['films_after']} | "
          f"2+ directors {join_report['films_2plus_directors']} | "
          f"no director {join_report['films_no_director']} | "
          f"no lead {join_report['films_cast_but_no_lead'] + join_report['films_no_cast_rows']}")
    films = apply_cleaning(films_talent)                              # stage 6
    kpis = both_windows(films)                                          # stage 7

    heading("QUALITY CHECK")
    checks = spot_check(films, sample_ids=None)                         # stage 9

    heading("LOAD")
    print(f"All outputs are in {config.OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as not_built:
        sys.exit(f"\nStopped: {not_built}. Later stages wait until it is built.")