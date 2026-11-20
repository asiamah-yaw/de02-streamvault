"""Run the StreamVault pipeline end to end.

Usage:  python run_pipeline.py                     (full run)
        python run_pipeline.py --skip-spotcheck    (offline: no live spot-check)
Needs:  the TMDB_API_KEY environment variable (see README).
Every run writes outputs/stage_timings.csv: seconds per stage, for diagnosis.
"""
import os
import sys
import time

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

TIMINGS = {}


def timed(stage, func, *args, **kwargs):
    """Run one stage and record its seconds (computation only; CSV writes are outside)."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    TIMINGS[stage] = round(time.perf_counter() - start, 3)
    return result


def check_api_key():
    """Stop at once, with a clear message, if the API key is missing."""
    if not os.environ.get(config.API_KEY_ENV_VAR):
        sys.exit(f"{config.API_KEY_ENV_VAR} is not set. See README, step 4.")


def heading(title):
    """Print an ETL section heading so the run shows where it is."""
    print(f"\n== {title} ==")


def main():
    run_start = time.perf_counter()
    check_api_key()
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    heading("EXTRACT")
    # Stage 1 - load and classify the id list
    fetchable, quarantine = timed("1_load", load_and_classify_ids, config.ID_LIST_PATH)
    classified = pd.concat([fetchable, quarantine]).sort_values("row_number")
    classified.to_csv(config.OUTPUT_DIR / "ids_classified.csv", index=False)
    quarantine.to_csv(config.OUTPUT_DIR / "quarantine.csv", index=False)
    print(f"[1 load] {len(classified)} rows read | {len(fetchable)} fetchable "
          f"| {len(quarantine)} quarantined -> outputs/quarantine.csv")

    # Stage 2 - fetch details and credits (cache first)
    manifest = timed("2_fetch", fetch_all, fetchable["movie_id"].tolist())
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
    # Stage 3 - flatten nested JSON into films, cast, crew
    found = movies.loc[movies["status"].eq(200), "movie_id"].tolist()   # only the films on this list
    films, cast, crew, flat_report = timed("3_flatten", build_tables, config.RAW_DIR, found)
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
    quality, quality_flags, quality_skew = timed("5_quality", quality_report, films, manifest, quarantine)
    quality.to_csv(config.OUTPUT_DIR / "quality_report.csv", index=False)
    quality_flags.to_csv(config.OUTPUT_DIR / "quality_flags.csv", index=False)
    quality_skew.to_csv(config.OUTPUT_DIR / "quality_skew.csv", index=False)
    print(f"[5 quality] {len(quality)} checks | {quality_flags['movie_id'].nunique()} films flagged "
          "-> outputs/quality_report.csv, quality_flags.csv, quality_skew.csv")

    heading("TRANSFORM")
    # Stage 4 - join lead actor and directors onto films
    films_talent, film_directors, film_leads, job_counts, join_report = timed(
        "4_join", join_talent, films, cast, crew, manifest)
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

    # Stage 6 - clean: exclusions, zero rule, franchise label, window, positions
    films_clean, excluded, clean_report = timed("6_clean", apply_cleaning, films_talent, quality_flags)
    films_clean.to_csv(config.OUTPUT_DIR / "films_clean.csv", index=False)
    excluded.to_csv(config.OUTPUT_DIR / "excluded_films.csv", index=False)
    clean_report.to_csv(config.OUTPUT_DIR / "cleaning_report.csv", index=False)
    print(f"[6 clean] films {len(films_talent)} -> {len(films_clean)} | excluded {len(excluded)} "
          "-> outputs/films_clean.csv, excluded_films.csv, cleaning_report.csv")

    # Stage 7 - KPIs for both windows (decisions fixed before results were viewed)
    kpis = timed("7_kpis", both_windows, films_clean, film_directors, film_leads)
    for name, table in kpis.items():
        table.to_csv(config.OUTPUT_DIR / f"{name}.csv", index=False)
    verdicts = kpis["kpi_comparison"]
    print("[7 kpis] " + " | ".join(f"{w}: {v}" for w, v in zip(verdicts["window"], verdicts["verdict"]))
          + " -> outputs/kpi_*.csv, shortlist_*.csv, talent_*.csv, deal_note.csv")

    heading("QUALITY CHECK")
    # Stage 9 - spot-check against the live API (uses the films as TMDb gave them).
    # --skip-spotcheck runs fully offline: used by the timing test, or by Adjoa without a connection.
    if "--skip-spotcheck" in sys.argv:
        print("[9 spot-check] skipped (--skip-spotcheck)")
    else:
        checks = timed("9_spotcheck", spot_check, films, films_clean, film_directors, film_leads, manifest, kpis)
        for name, table in checks.items():
            table.to_csv(config.OUTPUT_DIR / f"{name}.csv", index=False)
        s = checks["spotcheck_summary"].set_index("measure")["value"]
        print(f"[9 spot-check] {s['films_compared_live']} films compared live | {s['live_calls']} calls | "
              f"moves the recommendation: {s['moves_recommendation']} ({s['impact_detail']}) "
              "-> outputs/spotcheck.csv, spotcheck_summary.csv")

    heading("LOAD")
    TIMINGS["total_in_process"] = round(time.perf_counter() - run_start, 3)
    (pd.Series(TIMINGS, name="seconds").rename_axis("stage").reset_index()
       .to_csv(config.OUTPUT_DIR / "stage_timings.csv", index=False))
    print(f"[timing] " + " | ".join(f"{k} {v:.2f}s" for k, v in TIMINGS.items())
          + " -> outputs/stage_timings.csv")
    print(f"All outputs are in {config.OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as not_built:
        sys.exit(f"\nStopped: {not_built}. Later stages wait until it is built.")