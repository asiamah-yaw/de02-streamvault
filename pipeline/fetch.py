"""Stage 2: fetch movie details and credits from TMDb, with a disk cache."""


def fetch_all(movie_ids):
    """Fetch /movie/{id} and /movie/{id}/credits for every id.

    Takes:   list of unique, valid TMDb ids
    Returns: manifest DataFrame, one row per call
             (movie_id, endpoint, status, from_cache, fetched_at)
    Asserts: every id appears in the manifest
             ok + not_found == ids requested
    """
    raise NotImplementedError("Stage 2 - built in Phase 2")