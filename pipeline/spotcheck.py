"""Stage 9 - spot-check our output against the live API, and say whether anything moves the answer.

Takes:   films (stage 3, raw), films_clean (stage 6), film_directors and film_leads (stage 4),
         manifest (stage 2), kpis (stage 7)
Returns: {"spotcheck": one row per film x field, "spotcheck_summary": one row per measure}
Rules fixed before comparing (ADR): four slices chosen by rule; table vs cache = parse_check,
cache vs live = source_check; exact match except rating (tolerance); the analysis stays on the
cached snapshot; the cache is never overwritten; at most SPOTCHECK_MAX_CALLS live calls.
"""
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests

import config
from pipeline.fetch import make_session
from pipeline.kpis import _franchise_table, both_windows

EXACT = ["title", "release_date", "budget", "revenue", "status", "collection_id", "imdb_id",
         "director_ids", "top_billed_id"]
RESOLUTION = {
    "match": "none",
    "within_tolerance": "none: expected drift, recorded",
    "parsing_error": "fix the code, rerun, record as a finding",
    "source_changed": "analysis stays on the cached snapshot; refresh before the board if it moves the answer",
    "still_not_found": "none: stays excluded",
    "now_found": "report to Adjoa as a candidate to add (Q2); not added automatically",
    "unverified": "could not check; does not count as a match",
}


# ---------- reading one film's fields, the same way from the cache and from the live API ----------
def _doc_fields(movie, credits):
    """The compared fields from a movie document and its credits document."""
    coll = movie.get("belongs_to_collection")
    cast = [c for c in credits.get("cast", []) if c.get("order") is not None
            and c["order"] <= config.LEAD_MAX_ORDER]
    lead = sorted(cast, key=lambda c: (c["order"], c["id"]))[:1]
    directors = sorted({c["id"] for c in credits.get("crew", []) if c.get("job") in config.DIRECTOR_JOBS})
    return {"title": movie.get("title") or "", "release_date": movie.get("release_date") or "",
            "budget": str(movie.get("budget") or 0), "revenue": str(movie.get("revenue") or 0),
            "status": movie.get("status") or "", "collection_id": str(coll["id"]) if isinstance(coll, dict) else "",
            "imdb_id": movie.get("imdb_id") or "", "director_ids": "|".join(map(str, directors)),
            "top_billed_id": str(lead[0]["id"]) if lead else "", "vote_average": movie.get("vote_average")}


def _table_fields(films, film_directors, film_leads):
    """The same fields from our own tables (the raw stage 3 table, not the cleaned one)."""
    t = films.set_index("movie_id")
    out = pd.DataFrame({
        "title": t["title"].fillna(""),
        "release_date": t["release_date"].dt.strftime("%Y-%m-%d").fillna(""),
        "budget": t["budget"].fillna(0).astype("int64").astype(str),
        "revenue": t["revenue"].fillna(0).astype("int64").astype(str),
        "status": t["status"].fillna(""),
        "collection_id": t["collection_id"].astype("string").fillna(""),
        "imdb_id": t["imdb_id"].fillna(""),
        "vote_average": t["vote_average"]})
    d = film_directors.sort_values(["movie_id", "person_id"]).groupby("movie_id")["person_id"] \
        .agg(lambda s: "|".join(map(str, s)))
    lead = film_leads.sort_values(["movie_id", "cast_order", "person_id"]).drop_duplicates("movie_id") \
        .set_index("movie_id")["person_id"].astype(str)
    out["director_ids"] = d.reindex(out.index).fillna("")
    out["top_billed_id"] = lead.reindex(out.index).fillna("")
    return out


# ---------- choosing the sample, by rule ----------
def _crew_rows(movie_id):
    path = config.RAW_DIR / f"credits_{movie_id}.json"
    return len(json.loads(path.read_text()).get("crew", [])) if path.exists() else 0


def choose_sample(films_clean, film_directors, manifest, kpis):
    """Return [(movie_id, slice)] in priority order; every rule has a tie-break, so reruns pick the same films."""
    picks = []

    def add(ids, label):
        picks.extend((int(i), label) for i in ids)

    fc = films_clean[films_clean["has_revenue"]]
    # 1. messiest parsing: most directors, then most crew rows, then lowest id
    nd = film_directors.groupby("movie_id").size().rename("n").reset_index()
    nd = nd.sort_values(["n", "movie_id"], ascending=[False, True]).head(10)
    nd["crew"] = nd["movie_id"].map(_crew_rows)
    add(nd.sort_values(["n", "crew", "movie_id"], ascending=[False, False, True])["movie_id"].head(2), "1_parsing")
    # 2. extremes of the distribution
    by_rev = fc.sort_values(["revenue", "movie_id"], ascending=[False, True])
    add([by_rev["movie_id"].iloc[0], by_rev["movie_id"].iloc[-1]], "2_extreme")
    # 3. affected by a decision
    add([i for i in config.SENSITIVITY_FRANCHISE_CASES if i in set(fc["movie_id"])], "3_named_case")
    only = fc[fc["entry_position"].eq("only_listed")].sort_values(["revenue", "movie_id"], ascending=[False, True])
    add(only["movie_id"].head(1), "3_only_listed")
    for cid in kpis["deal_note"]["collection_id"].dropna().unique():
        members = fc[fc["collection_id"].eq(cid)].sort_values(["revenue", "movie_id"], ascending=[False, True])
        add(members["movie_id"].head(config.SPOTCHECK_SLICE_CAP), "3_deal_franchise")
    standalones = fc[~fc["is_franchise"]].sort_values(["revenue", "movie_id"], ascending=[False, True])
    add(standalones["movie_id"].head(1), "3_top_standalone")
    ranked = _franchise_table(fc, pd.Series(True, index=fc.index))
    if len(ranked) > config.SHORTLIST_FRANCHISES:
        cid = ranked["collection_id"].iloc[config.SHORTLIST_FRANCHISES]
        members = fc[fc["collection_id"].eq(cid)].sort_values(["revenue", "movie_id"], ascending=[False, True])
        add(members["movie_id"].head(config.SPOTCHECK_SLICE_CAP), "3_first_franchise_outside_shortlist")
    add(standalones["movie_id"].iloc[config.SHORTLIST_STANDALONES:config.SHORTLIST_STANDALONES + 1],
        "3_first_standalone_outside_shortlist")
    chosen = {i for i, _ in picks}
    if not fc[fc["movie_id"].isin(chosen)]["release_year"].lt(config.WINDOW_CUTOFF_YEAR).any():
        old = fc[fc["release_year"].lt(config.WINDOW_CUTOFF_YEAR)].sort_values(["revenue", "movie_id"], ascending=[False, True])
        add(old["movie_id"].head(1), "3_pre_cutoff")
    # 4. failed to fetch: every id the manifest recorded as not found
    movies = manifest[manifest["endpoint"].eq("movie")]
    add(movies.loc[movies["status"].eq(404), "movie_id"], "4_not_found")
    sample = pd.DataFrame(picks, columns=["movie_id", "slice"])
    return sample.groupby("movie_id", sort=False)["slice"].agg("+".join).reset_index()


# ---------- the live calls ----------
def _live(session, key, path):
    """One polite live GET. Returns (document or None, outcome)."""
    try:
        r = session.get(f"{config.API_BASE_URL}{path}", params={"api_key": key}, timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException as exc:          # timeouts, connection errors, retries exhausted
        return None, f"unverified ({type(exc).__name__})"
    finally:
        time.sleep(config.SLEEP_BETWEEN_CALLS)
    if r.status_code == 200:
        return r.json(), "ok"
    if r.status_code == 404:
        return None, "404"
    return None, f"unverified (HTTP {r.status_code})"


def _classify_source(field, cached, live):
    if field == "vote_average":
        if cached is None or live is None:
            return "match" if cached == live else "source_changed"
        diff = abs(float(cached) - float(live))
        return "match" if diff == 0 else ("within_tolerance" if diff <= config.SPOTCHECK_RATING_TOLERANCE else "source_changed")
    return "match" if cached == live else "source_changed"


def _shortlist_state(k):
    return {"verdicts": tuple(k["kpi_comparison"]["verdict"]),
            "top_franchise": tuple(k["deal_note"]["collection_id"]),
            "shortlist": frozenset(k["shortlist_franchise"]["collection_id"].tolist()
                                   + k["shortlist_standalone"]["movie_id"].tolist())}


def spot_check(films, films_clean, film_directors, film_leads, manifest, kpis, sample_ids=None):
    key = os.environ.get(config.API_KEY_ENV_VAR)
    stamp = datetime.now(timezone.utc)
    evidence = config.OUTPUT_DIR / "spotcheck_live" / stamp.strftime("%Y%m%dT%H%M%SZ")
    evidence.mkdir(parents=True, exist_ok=True)
    sample = choose_sample(films_clean, film_directors, manifest, kpis) if sample_ids is None \
        else pd.DataFrame({"movie_id": sample_ids, "slice": "override"})
    table = _table_fields(films, film_directors, film_leads)
    session, calls, rows = make_session(), 0, []

    for movie_id, slice_ in sample.itertuples(index=False):          # a handful of sampled films, not the table
        is_404 = "4_not_found" in slice_
        needed = 1 if is_404 else 2
        if calls + needed > config.SPOTCHECK_MAX_CALLS:
            rows.append({"movie_id": movie_id, "slice": slice_, "field": "all", "source_check": "unverified",
                         "resolution": RESOLUTION["unverified"] + " (call budget reached)"})
            continue
        live_movie, outcome = _live(session, key, f"/movie/{movie_id}")
        calls += 1
        if is_404:
            cls = {"404": "still_not_found", "ok": "now_found"}.get(outcome, "unverified")
            rows.append({"movie_id": movie_id, "slice": slice_, "field": "exists", "table": "excluded",
                         "cached": "404", "live": outcome, "parse_check": "n/a", "source_check": cls,
                         "resolution": RESOLUTION[cls]})
            continue
        live_credits, outcome_c = _live(session, key, f"/movie/{movie_id}/credits") if outcome == "ok" else (None, outcome)
        calls += 1 if outcome == "ok" else 0
        if live_movie is not None:
            (evidence / f"movie_{movie_id}.json").write_text(json.dumps(live_movie))
        if live_credits is not None:
            (evidence / f"credits_{movie_id}.json").write_text(json.dumps(live_credits))
        cached = _doc_fields(json.loads((config.RAW_DIR / f"movie_{movie_id}.json").read_text()),
                             json.loads((config.RAW_DIR / f"credits_{movie_id}.json").read_text()))
        live = _doc_fields(live_movie, live_credits) if (live_movie is not None and live_credits is not None) else None
        mine = table.loc[movie_id]
        for field in EXACT + ["vote_average"]:
            parse = "match" if (field == "vote_average" and float(mine[field]) == float(cached[field])) \
                or (field != "vote_average" and mine[field] == cached[field]) else "parsing_error"
            source = "unverified" if live is None else _classify_source(field, cached[field], live[field])
            worst = parse if parse == "parsing_error" else source
            rows.append({"movie_id": movie_id, "slice": slice_, "field": field, "table": mine[field],
                         "cached": cached[field], "live": None if live is None else live[field],
                         "parse_check": parse, "source_check": source, "resolution": RESOLUTION[worst]})
    result = pd.DataFrame(rows)

    # Does anything move the recommendation? Substitute live revenue; collection or status changes need a full rerun.
    changed = result[result["source_check"].eq("source_changed")]
    revenue = changed[changed["field"].eq("revenue")]
    structural = changed[changed["field"].isin(["collection_id", "status"])]
    moves, detail = False, "no decision-relevant change"
    if len(revenue):
        patched = films_clean.copy()
        new = revenue.set_index("movie_id")["live"].astype("int64")
        hit = patched["movie_id"].isin(new.index)
        patched.loc[hit, "revenue"] = patched.loc[hit, "movie_id"].map(new).astype("Int64")
        patched["has_revenue"] = patched["revenue"].fillna(0).gt(0)
        before, after = _shortlist_state(kpis), _shortlist_state(both_windows(patched, film_directors, film_leads))
        moved = [k for k in before if before[k] != after[k]]
        moves, detail = bool(moved), ("changes: " + ", ".join(moved)) if moved else "revenue changes do not move the answer"
    if len(structural):
        moves, detail = True, detail + "; collection or status changed: refresh the cache and rerun before relying on it"

    margins = {}
    for window, mask in {"all_years": pd.Series(True, index=films_clean.index),
                         "from_2000": films_clean["from_2000"].fillna(False).astype(bool)}.items():
        t = _franchise_table(films_clean[films_clean["has_revenue"]], mask[films_clean["has_revenue"]])
        margins[window] = round(t["median_revenue"].iloc[0] / t["median_revenue"].iloc[1], 2) if len(t) > 1 else None

    stamps = manifest["fetched_at"]
    fetched = (pd.to_datetime(stamps, unit="s", errors="coerce", utc=True) if pd.api.types.is_numeric_dtype(stamps)
               else pd.to_datetime(stamps, errors="coerce", utc=True)).max()
    compared = result[~result["field"].isin(["exists", "all"]) & result["source_check"].ne("unverified")]
    films_checked = compared["movie_id"].nunique()             # films actually compared with the live API
    summary = {
        "films_sampled": int(sample["movie_id"].nunique()), "films_compared_live": int(films_checked),
        "live_calls": calls, "call_budget": config.SPOTCHECK_MAX_CALLS,
        **{f"parse_{k}": int(v) for k, v in result["parse_check"].value_counts().items()},
        **{f"source_{k}": int(v) for k, v in result["source_check"].value_counts().items()},
        "moves_recommendation": moves, "impact_detail": detail,
        "top_two_franchise_margin_all_years": margins["all_years"],
        "top_two_franchise_margin_from_2000": margins["from_2000"],
        "data_fetched_as_of": f"{fetched:%Y-%m-%d}", "checked_at": f"{stamp:%Y-%m-%d %H:%M} UTC",
        "evidence_folder": str(evidence.relative_to(config.OUTPUT_DIR)),
        "claim_limit_1": "both sides come from TMDb: this shows we reproduce TMDb, not that TMDb is correct",
        "claim_limit_2": f"risk-weighted sample of {films_checked} films, not the whole list; with no discrepancies the rate could still be up to about {round(100 * (1 - 0.05 ** (1 / max(films_checked, 1))))}%",
        "claim_limit_3": "'nearly failed to fetch' is checked through not-found ids only; retries are not recorded",
    }
    return {"spotcheck": result,
            "spotcheck_summary": pd.Series(summary, name="value").rename_axis("measure").reset_index()}