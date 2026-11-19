"""All settings for the StreamVault pipeline, in one place.

Change a value here, not inside the pipeline code.
"""
import os
from pathlib import Path

# --- Paths (relative to the project root, so they work on any machine) ---
# The two environment variables are optional; only the timing test sets them, to run on
# synthetic data in a temporary folder. Normal runs use the defaults.
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("STREAMVAULT_DATA_DIR", PROJECT_ROOT / "data"))
ID_LIST_PATH = Path(os.environ.get("STREAMVAULT_ID_LIST", DATA_DIR / "id_list.csv"))  # client input, never edited; a quarter's list can be pointed to instead
RAW_DIR = DATA_DIR / "raw"                   # cached API responses (not in git)
OUTPUT_DIR = Path(os.environ.get("STREAMVAULT_OUTPUT_DIR", PROJECT_ROOT / "outputs"))

# --- Input file ---
ID_COLUMN = "tmdb_id"                        # the only column in id_list.csv

# --- Analysis ---
WINDOW_CUTOFF_YEAR = 2000                    # brief: all years vs 2000-onward
MIN_GROUP_SIZE = 5                           # independent units per group (ADR; set after group sizes were known)

# --- TMDb API ---
API_KEY_ENV_VAR = "TMDB_API_KEY"             # the key is read from here, never stored
API_BASE_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = (3.05, 10)                 # (connect seconds, read seconds)
MAX_RETRIES = 5                              # for 429 / 5xx only
BACKOFF_FACTOR = 1                           # waits roughly 1, 2, 4, 8... seconds
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
SLEEP_BETWEEN_CALLS = 0.25                   # seconds; be polite to a free API
USER_AGENT = "de02-streamvault-lab (student project)"

# --- Performance (Phase 8) - set before measuring; see ADR ---
TIME_BUDGET_SECONDS = 10                     # cached rerun of stages 1-7 at 500 titles ("live in a meeting")
TIME_HEADROOM_SECONDS = 5                    # median at 500 must be under this, so a 2x slower laptop still passes
LINEAR_TOLERANCE = 1.5                       # seconds per title at 5,000 at most 1.5x that at 500
TIMING_RUNS = 5                              # runs per size; run 1 reported separately
TIMING_SIZES = [500, 5000]                   # synthetic list sizes (plus the real 112)


# --- TMDb fields the pipeline depends on (Phase 3) ---
# Each mapping is {TMDb field: our column name}; renaming happens here, once.
FILM_FIELDS = {
    "id": "movie_id",
    "title": "title",
    "release_date": "release_date",
    "budget": "budget",
    "revenue": "revenue",
    "runtime": "runtime",
    "status": "status",
    "vote_average": "vote_average",
    "vote_count": "vote_count",
    "popularity": "popularity",
    "original_language": "original_language",
    "imdb_id": "imdb_id",
}
COLLECTION_FIELD = "belongs_to_collection"   # nested {id, name}, or null
GENRES_FIELD = "genres"                       # list of {id, name}

CAST_FIELDS = {
    "credit_id": "credit_id",                 # unique key for one cast credit
    "id": "person_id",
    "name": "name",
    "character": "character",
    "order": "cast_order",                    # 0 = top-billed
}
CREW_FIELDS = {
    "credit_id": "credit_id",                 # unique key for one crew credit
    "id": "person_id",
    "name": "name",
    "department": "department",
    "job": "job",
}

# --- Talent (Phase 4) - assumptions; see ADR ---
LEAD_MAX_ORDER = 0                           # 0 = top-billed only; 2 would mean top 3
DIRECTOR_JOBS = ["Director"]                 # alternative: ["Director", "Co-Director"]
MIN_TALENT_FILMS = 3                         # talent needs 3+ films (ADR; set from stage 4 counts, no revenue)

DATE_FIELDS = ["release_date"]                       # parsed to dates
INT_FIELDS = ["budget", "revenue", "runtime", "vote_count"]  # nullable whole numbers
KNOWN_STATUSES = ["Rumored", "Planned", "In Production",
                  "Post Production", "Released", "Canceled"]  # checked in stage 5

# --- Profiling (Phase 5) - thresholds are assumptions; findings say so ---
LOW_VOTE_COUNT = 50                          # ratings below this are not trusted
SEQUEL_PATTERN = r"(?:\s\d+|\s(?:II|III|IV|V|VI))(?::|$)|\bPart\b"   # review list only

# --- Cleaning (Phase 6) - decisions; see ADRs ---
EXCLUDE_CHECKS = ["status_not_released", "released_after_fetch"]   # stage 5 flags that exclude a film
FRANCHISE_OVERRIDES = {}     # {movie_id: reason} forces a film to franchise; empty by default (ADR)

# --- KPIs (Phase 7) - fixed before any result was viewed; see ADRs ---
MIN_TALENT_CONTEXTS = 2      # films from 2+ different collections/standalones, so a person is not just one franchise
MIN_SHORTLIST_FILMS = 3      # a franchise needs 3+ listed films to be shortlisted
SHORTLIST_FRANCHISES = 3     # brief: three strongest franchise targets
SHORTLIST_STANDALONES = 5    # brief: five strongest standalones
SENSITIVITY_FRANCHISE_CASES = {429: "The Good, the Bad and the Ugly: third film of a trilogy, no TMDb collection (found by reading the list)"}


# --- Spot-check (Phase 9) - fixed before comparing; see ADR ---
SPOTCHECK_MAX_CALLS = 50            # live calls per spot-check, at most (polite to a free API)
SPOTCHECK_RATING_TOLERANCE = 0.1    # ratings drift daily; anything else must match exactly
SPOTCHECK_SLICE_CAP = 5             # at most 5 films from any one franchise slice