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