"""All settings for the StreamVault pipeline, in one place.

Change a value here, not inside the pipeline code.
"""
from pathlib import Path

# --- Paths (relative to the project root, so they work on any machine) ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ID_LIST_PATH = DATA_DIR / "id_list.csv"     # client input, never edited
RAW_DIR = DATA_DIR / "raw"                   # cached API responses (not in git)
OUTPUT_DIR = PROJECT_ROOT / "outputs"        # everything the pipeline produces

# --- Input file ---
ID_COLUMN = "tmdb_id"                        # the only column in id_list.csv

# --- Analysis ---
WINDOW_CUTOFF_YEAR = 2000                    # brief: all years vs 2000-onward
MIN_GROUP_SIZE = None                        # decided in Phase 7 (KPIs)

# --- TMDb API ---
API_KEY_ENV_VAR = "TMDB_API_KEY"             # the key is read from here, never stored
API_BASE_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = (3.05, 10)                 # (connect seconds, read seconds)
MAX_RETRIES = 5                              # for 429 / 5xx only
BACKOFF_FACTOR = 1                           # waits roughly 1, 2, 4, 8... seconds
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
SLEEP_BETWEEN_CALLS = 0.25                   # seconds; be polite to a free API
USER_AGENT = "de02-streamvault-lab (student project)"

# --- Performance ---
TIME_BUDGET_SECONDS = None                   # decided in Phase 8 (timing)


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
MIN_TALENT_FILMS = None                      # set in Phase 7, from the counts stage 4 prints

DATE_FIELDS = ["release_date"]                       # parsed to dates
INT_FIELDS = ["budget", "revenue", "runtime", "vote_count"]  # nullable whole numbers
KNOWN_STATUSES = ["Rumored", "Planned", "In Production",
                  "Post Production", "Released", "Canceled"]  # checked in stage 5

# --- Profiling (Phase 5) - thresholds are assumptions; findings say so ---
LOW_VOTE_COUNT = 50                          # ratings below this are not trusted
SEQUEL_PATTERN = r"(?:\s\d+|\s(?:II|III|IV|V|VI))(?::|$)|\bPart\b"   # review list only