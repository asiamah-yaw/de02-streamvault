# StreamVault Licensing Analysis

Evidence for one decision: should StreamVault spend its $14M licensing budget on
franchise bundles or on standalone films? This pipeline pulls film data from the
public TMDb API for the candidate list in `data/id_list.csv`, checks and cleans it,
and compares franchise and standalone titles across all years and from 2000 onward.

## Setup and run

1. Clone the repository
   ```
   git clone https://github.com/asiamah-yaw/de02-streamvault
   cd de02-streamvault
   ```
2. Create and activate a virtual environment (Python 3.11 or newer)
   ```
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate.bat
   ```
3. Install the dependencies
   ```
   pip install -r requirements.txt
   ```
4. Set your own free TMDb API key (themoviedb.org > Settings > API)
   - Linux / Mac: add `export TMDB_API_KEY="your-key"` to `~/.bashrc`, then run `source ~/.bashrc`
   - Windows: `setx TMDB_API_KEY "your-key"`, then open a new terminal

   The key is read from the environment and is never stored in this repository.
5. Run the pipeline
   ```
   python run_pipeline.py
   ```

## What a run does

- **First run:** fetches movie details and credits for every valid id (a few minutes,
  throttled on purpose) and caches each response in `data/raw/`.
- **Later runs:** read from the cache and make no API calls.
- Results are written to `outputs/`.

## Profiling notebook

`profiling/profiling.ipynb` explores the data using the pipeline's own functions.
Run the pipeline first, then install `requirements-dev.txt` to open the notebook.

## To be completed

- How the stages map to Extract, Validate, Transform, Quality check and Load
- What each file in `outputs/` contains
- Where to find the deliverables
- Use of AI tools