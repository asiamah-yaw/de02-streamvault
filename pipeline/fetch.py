"""Stage 2: fetch movie details and credits from TMDb, with a disk cache."""
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config


def make_session():
    """One reusable connection with a polite retry policy (Moodle 7, 8)."""
    session = requests.Session()
    retry = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.BACKOFF_FACTOR,
        status_forcelist=config.RETRY_STATUS_CODES,   # 429 and 5xx only, never 404
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = config.USER_AGENT
    return session


def fetch_one(session, movie_id, endpoint, key):
    """Return one manifest row for one call, using the cache when possible.

    endpoint is "movie" or "credits".
    """
    ok_file = config.RAW_DIR / f"{endpoint}_{movie_id}.json"
    missing_file = config.RAW_DIR / f"{endpoint}_{movie_id}.404"

    # Cache first: a saved answer means no API call (Moodle 8.1).
    # Look for a saved 200 response, then a saved 404; either one is returned without a call or a pause.
    for cached, status in ((ok_file, 200), (missing_file, 404)):
        if cached.exists():
            saved_at = datetime.fromtimestamp(cached.stat().st_mtime, tz=timezone.utc)
            return {"movie_id": movie_id, "endpoint": endpoint, "status": status,
                    "from_cache": True, "fetched_at": saved_at.isoformat()}

    url = f"{config.API_BASE_URL}/movie/{movie_id}"
    if endpoint == "credits":
        url += "/credits"
    try:
        response = session.get(url, params={"api_key": key}, timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException as exc:  # the original message holds the URL, and the URL holds the key
        raise RuntimeError(f"TMDb request failed for {endpoint} {movie_id} ({type(exc).__name__}). "
                           "Every response so far is saved, so a rerun resumes from here.") from None

    if response.status_code == 200:
        ok_file.write_text(json.dumps(response.json()), encoding="utf-8")
    elif response.status_code == 404:
        missing_file.write_text(response.text, encoding="utf-8")
    else:                                     # e.g. 401 bad key: stop loudly, without printing the key
        raise RuntimeError(f"TMDb answered HTTP {response.status_code} for {endpoint} {movie_id}"
                           f"{' (the API key is wrong)' if response.status_code == 401 else ''}.")

    time.sleep(config.SLEEP_BETWEEN_CALLS)    # polite pause after every live call, 200 and 404 alike
    return {"movie_id": movie_id, "endpoint": endpoint, "status": response.status_code,
            "from_cache": False, "fetched_at": datetime.now(timezone.utc).isoformat()}


def fetch_all(movie_ids):
    """Fetch /movie/{id} and /movie/{id}/credits for every id.

    Takes:   list of unique, valid TMDb ids
    Returns: manifest DataFrame, one row per call
             (movie_id, endpoint, status, from_cache, fetched_at)
    Asserts: every id appears in the manifest
             ok + not_found == ids requested
    """
    key = os.environ[config.API_KEY_ENV_VAR]
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = make_session()

    rows = []
    for movie_id in movie_ids:                # one call per id is unavoidable
        movie_row = fetch_one(session, movie_id, "movie", key)
        rows.append(movie_row)
        if movie_row["status"] == 200:
            rows.append(fetch_one(session, movie_id, "credits", key))
        else:                                 # film not found: skip a pointless call
            rows.append({"movie_id": movie_id, "endpoint": "credits", "status": None,
                         "from_cache": False, "fetched_at": None})

    manifest = pd.DataFrame(rows)
    manifest["status"] = manifest["status"].astype("Int64")

    movies = manifest.loc[manifest["endpoint"].eq("movie")]
    assert set(movies["movie_id"]) == set(movie_ids), "an id is missing from the manifest"
    assert movies["status"].isin([200, 404]).sum() == len(movie_ids), "unaccounted fetch result"

    return manifest