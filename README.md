# StreamVault licensing analysis

Should StreamVault spend its licensing budget on franchise bundles or standalone hits? This project fetches the candidate films from The Movie Database (TMDb), checks and cleans the data, compares franchises with standalones for all years and from 2000 onward, and produces a shortlist, a talent read and a deal note.

> This product uses the TMDB API but is not endorsed or certified by TMDB. All film data comes from TMDb.

## Deliverables

| Document | What it is |
|---|---|
| [client_memo.md](client_memo.md) | One-page memo to Kwame: recommendation, shortlist, both time periods, deal note, what I could not stand behind |
| [data_findings.md](data_findings.md) | Data diagnosis: every problem found, ranked by its measured effect, and where all 127 candidate rows went |
| [decisions/](decisions/README.md) | Decision notes: 8 decision records, smaller decisions, and what survives a 500-title rerun |
| [timing_report.md](timing_report.md) | Measured run time against the 10-second budget at 112, 500 and 5,000 titles |
| [questions.md](questions.md) | Questions the data cannot settle, with the default applied and its cost if wrong |
| [improvement.md](improvement.md) | The improvement beyond the brief: a run-to-run change report |

## Setup

Needs Python 3.11 or newer (pandas 3 does not install on older versions); **tested on Python 3.14.4 only**, under WSL Ubuntu. Needs a free TMDb API key and network access for the first run.

1. Clone the repository and enter it:
   ```bash
   git clone https://github.com/asiamah-yaw/de02-streamvault.git
   cd de02-streamvault
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```
3. Install the exact package versions:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your TMDb key as an environment variable (never in a file in this folder):
   ```bash
   export TMDB_API_KEY="your-key-here"            # Linux/macOS; add to ~/.bashrc to keep it
   ```
   On Windows PowerShell: `setx TMDB_API_KEY "your-key-here"`, then open a new terminal.

   Error messages never show the key: if a call fails, the run names the film and the kind of error only.

## Run

```bash
python run_pipeline.py                     # full run, including a live spot-check of 13 films
python run_pipeline.py --skip-spotcheck    # no live spot-check (fully offline only after the first fetch)
python -m pipeline.timing                  # measure run time at 112, 500 and 5,000 titles
python -m pipeline.compare_runs            # what changed since the last saved result (see improvement.md)
```

- **First run** (needs the network): fetches details and credits for every candidate (229 calls) and saves each response in `data/raw/`. Measured in a clean clone on 20 November 2026: 118 seconds, about 2 minutes.
- **Every later run** reads the saved responses and makes no calls for the analysis. Measured (timing_report.md, excluding the fetch and the live spot-check): 1.58 seconds for this year's list, 3.40 seconds at 500 titles.
- **Reruns are identical**, apart from `outputs/stage_timings.csv` and the live spot-check files, which record when they ran. Checked by comparing file fingerprints (md5) of every other output across two reruns.
- **The live spot-check** makes about 30 calls and compares our tables with TMDb as it is today.

**A good run ends like this:**
```
[6 clean] films 112 -> 112 | excluded 0 -> outputs/films_clean.csv, excluded_films.csv, cleaning_report.csv
[7 kpis] all_years: franchise | from_2000: franchise -> outputs/kpi_*.csv, shortlist_*.csv, talent_*.csv, deal_note.csv
...
[9 spot-check] 13 films compared live | 31 calls | moves the recommendation: False (no decision-relevant change) -> ...
```
A `WARNING: THE RECOMMENDATION CHANGES BETWEEN WINDOWS` line would mean the two periods disagree. Without a key, the run stops at once with `TMDB_API_KEY is not set. See README, step 4.`

Optional exploration: `pip install -r requirements-dev.txt`, then open `profiling/profiling.ipynb`. The notebook calls the same functions as the pipeline and re-implements nothing.

## What the pipeline does

Run order is top to bottom. The design stage numbers follow the course's ten-stage plan; profiling (5) runs before the join (4) on purpose, so the data is examined as it arrived.

| Section | Design stage | File | What it does | Main outputs |
|---|---|---|---|---|
| Extract | 1 | `pipeline/load_ids.py` | Reads the 127 rows as text, classifies each, quarantines unusable rows and repeats with a reason | `ids_classified.csv`, `quarantine.csv` |
| Extract | 2 | `pipeline/fetch.py` | Fetches details and credits once per film, with timeouts, retries and a polite pause; records every "not found" | `fetch_manifest.csv` |
| Validate | 3 | `pipeline/flatten.py` | Turns the nested responses into three tables: one row per film, per cast credit, per crew credit | `films.csv`, `cast.csv`, `crew.csv` |
| Validate | 5 | `pipeline/quality.py` | Profiles the films as received; reports problems, fixes nothing | `quality_report.csv`, `quality_flags.csv`, `quality_skew.csv` |
| Transform | 4 | `pipeline/join.py` | Attaches the lead actor and directors; proves no film was dropped or repeated | `films_with_talent.csv`, `film_directors.csv`, `join_report.csv` |
| Transform | 6 | `pipeline/clean.py` | Applies the franchise label, the insurance rules and series positions; counts every change | `films_clean.csv`, `cleaning_report.csv` |
| Transform | 7 | `pipeline/kpis.py` | Both time periods, the verdict rule, alternatives, shortlists, talent, deal note | `kpi_*.csv`, `shortlist_*.csv`, `talent_*.csv`, `deal_note.csv` |
| Quality check | 9 | `pipeline/spotcheck.py` | Re-fetches risky films live and classifies every difference | `spotcheck.csv`, `spotcheck_summary.csv` |
| Measure | 8 | `pipeline/timing.py` | Separate command: times cached reruns at three sizes | `timing_report.md` |

All settings and thresholds are in `config.py`. Every output goes to `outputs/`; `outputs/stage_timings.csv` records the seconds per stage on every run.

## Rerunning next quarter (for Adjoa)

1. **Archive last quarter's data so everything is fetched fresh:** `mv data/raw data/raw_2026-11-19`. Without this, films already saved are not fetched again, and their figures would stay as they were when first fetched. Saved films that are not on the new list are ignored, so they never enter the analysis.
2. **Save the new list as its own file** (one column, `tmdb_id`), for example `lists/2027-q1.csv`, and point the run at it. The client's original `data/id_list.csv` stays untouched:
   ```bash
   export STREAMVAULT_ID_LIST=lists/2027-q1.csv     # stays set in this terminal, for steps 2 and 3
   python run_pipeline.py
   ```
   A new 500-title list takes about 8 to 9 minutes the first time (estimate: about 1,000 calls at the 0.52 seconds per call measured in the clean clone), then about 3.4 seconds per rerun.
3. **See what changed:** `python -m pipeline.compare_runs` compares this run with the last saved result (the committed reference is `snapshots/2026-11-19/`); `python -m pipeline.compare_runs --save` saves this run as the next quarter's starting point.
4. **Read what needs a person's judgement:**
   - `outputs/quarantine.csv` and the "not found" ids printed by stage 2: what were they meant to be?
   - `outputs/quality_flags.csv`, check `no_collection_title_looks_like_sequel`: franchise entries TMDb does not group.
   - `outputs/talent_*.csv`: people whose "contexts" are really one connected series.
5. **Check the warning line:** the run prints a warning if the two time periods disagree.

What runs unchanged, what needs your input and what stops being valid are listed in [decisions/README.md](decisions/README.md#what-survives-when-adjoa-reruns-this-on-500-titles).

## What is in the repository, and what is not

- **Committed:** the code, the settings, the candidate list (`data/id_list.csv`, unchanged from the client), the documents, and a small reference result (`snapshots/2026-11-19/`: verdicts, shortlists, deal note, box office per film, the candidate-list fingerprint and the fetch dates).
- **Not committed, rebuilt by running:** `data/raw/` and any archived `data/raw_<date>/` (the saved TMDb responses), and `outputs/`.
- **Never committed:** the API key, the virtual environment and scratch work (see `.gitignore`).

**Why the TMDb responses are not committed (ADR-002).** TMDb's terms, as quoted on TMDb's own support forum (read 19 November 2026; the terms page itself could not be retrieved automatically), say you shall not "cache any TMDb metadata or photos other than for reasonable periods in order to provide your service". Saving responses to run this analysis fits that; republishing all of them in a public repository is not clearly allowed. TMDb's free key is also for non-commercial use with attribution: this project is coursework, but StreamVault's own quarterly use would need TMDb's commercial terms (question Q6).

A fresh clone therefore needs a TMDb key and network access for the first fetch, and its figures can differ slightly from the memo's if TMDb has changed since 19 November 2026; `python -m pipeline.compare_runs` reports any difference against the committed reference. That reference was saved before three small code fixes on 20 November 2026 (error messages never show the key; only films on the current list are read from the saved responses; the change report fingerprints the list the run actually used), so the comparison also reports that the code changed. The results are identical.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```
The tests use small hand-made data, need no key and no network, and check five things: every candidate row is accounted for (reconciliation), bad ids get the right reason, the zero rule works both ways (including a run with nothing to exclude, a case that once broke), the join refuses to duplicate a film, and the change report names each kind of change.

## Use of AI

I used an AI tool to explain concepts, review my plans against the brief and rubric, suggest code that I then ran, tested and checked against my own outputs, and suggest wording for the documents. Every decision, number and conclusion was checked against this pipeline's results, and I can explain each one.