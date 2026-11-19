"""Stage 8 - measure a cached rerun against the time budget, at 112, 500 and 5,000 titles.

Usage:  python -m pipeline.timing
Never calls the API: synthetic lists are built in a temporary folder from the cached files, and
every run uses a dummy key, so a live call would fail loudly. Real outputs/ is never written to.
Writes outputs/timing_report.csv and timing_report.md (house measurement template).
"""
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

import config

OFFSET = 10_000_000          # synthetic copy k gets ids base + k * OFFSET, so nothing collides
DUMMY_KEY = "timing-test-no-network"


def _copy_doc(doc, k, kind):
    """Rewrite one cached JSON document as synthetic copy k (k = 0 keeps the original)."""
    doc = json.loads(json.dumps(doc))                       # deep copy
    if k == 0:
        return doc
    doc["id"] = doc["id"] + k * OFFSET
    if kind == "movie":
        doc["imdb_id"] = f"{doc.get('imdb_id') or 'tt'}-copy{k}"
        doc["title"] = f"{doc.get('title')} [copy {k}]"
        if isinstance(doc.get("belongs_to_collection"), dict):
            doc["belongs_to_collection"]["id"] += k * OFFSET
            doc["belongs_to_collection"]["name"] += f" [copy {k}]"
    else:
        for credit in doc.get("cast", []) + doc.get("crew", []):
            credit["credit_id"] = f"{credit['credit_id']}-copy{k}"
            credit["id"] = credit["id"] + k * OFFSET
    return doc


def build_synthetic(n_titles, data_dir):
    """A candidate list of n_titles rows, made from the cached films, plus a few planted defects."""
    raw = data_dir / "raw"
    raw.mkdir(parents=True)
    base_ids = sorted(int(p.stem.split("_")[1]) for p in config.RAW_DIR.glob("movie_*.json"))
    defects = ["", "N/A", str(base_ids[0]), str(base_ids[1])]          # blank, text, two repeats
    missing = [9_999_000_000 + i for i in range(3)]                    # three ids that are 'not found'
    n_films = n_titles - len(defects) - len(missing)
    ids = []
    for i in range(n_films):
        k, base = divmod(i, len(base_ids))
        base_id = base_ids[base]
        new_id = base_id + k * OFFSET
        for kind in ["movie", "credits"]:
            doc = json.loads((config.RAW_DIR / f"{kind}_{base_id}.json").read_text())
            doc = _copy_doc(doc, k, kind)
            if kind == "movie" and k > 0 and i % 50 == 0:
                doc["revenue"] = 0                                     # exercises the zero rule
            if kind == "movie" and k > 0 and i % 97 == 0:
                doc["status"] = "Planned"                              # exercises the exclusion path
            (raw / f"{kind}_{new_id}.json").write_text(json.dumps(doc))
        ids.append(str(new_id))
    for m in missing:
        (raw / f"movie_{m}.404").write_text("")
    rows = ids + [str(m) for m in missing] + defects
    pd.DataFrame({config.ID_COLUMN: rows}).to_csv(data_dir / "id_list.csv", index=False)
    return len(rows)


def run_once(data_dir, out_dir):
    """Wall clock of the command Adjoa types, from the cache, with no network."""
    env = {**os.environ, "STREAMVAULT_DATA_DIR": str(data_dir), "STREAMVAULT_OUTPUT_DIR": str(out_dir),
           config.API_KEY_ENV_VAR: DUMMY_KEY}
    start = time.perf_counter()
    done = subprocess.run([sys.executable, "run_pipeline.py", "--skip-spotcheck"], cwd=config.PROJECT_ROOT,
                          env=env, capture_output=True, text=True)
    seconds = time.perf_counter() - start
    if done.returncode != 0:
        raise RuntimeError(f"pipeline failed during timing:\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}")
    return seconds, done.stdout


def check_correctness(stdout, out_dir):
    """The run must make 0 live calls, reach stage 7, and account for every row."""
    classified = pd.read_csv(out_dir / "ids_classified.csv")
    quarantine = pd.read_csv(out_dir / "quarantine.csv")
    manifest = pd.read_csv(out_dir / "fetch_manifest.csv")
    clean = pd.read_csv(out_dir / "films_clean.csv")
    excluded = pd.read_csv(out_dir / "excluded_films.csv")
    not_found = int((manifest["endpoint"].eq("movie") & manifest["status"].eq(404)).sum())
    return {"zero_live_calls": " 0 live calls " in stdout,
            "reached_stage_7": "[7 kpis]" in stdout,
            "rows_reconcile": len(classified) == len(quarantine) + not_found + len(clean) + len(excluded),
            "zero_rule_fired": int(pd.read_csv(out_dir / "cleaning_report.csv")
                                   .set_index("rule").loc["zero_revenue_to_missing", "rows_affected"]),
            "films_excluded": len(excluded)}


def first_fetch_estimate(n_titles):
    """From the real manifest: seconds per live call x calls needed (2 per found film, 1 per missing)."""
    files = sorted(config.RAW_DIR.glob("*.json")) + sorted(config.RAW_DIR.glob("*.404"))
    stamps = pd.Series(sorted(p.stat().st_mtime for p in files))
    per_call = float(stamps.diff().median())      # median gap: robust to files written at another time
    manifest = pd.read_csv(config.OUTPUT_DIR / "fetch_manifest.csv")
    movies = manifest[manifest["endpoint"].eq("movie")]
    found_share = movies["status"].eq(200).mean()
    calls = 2 * n_titles * found_share + n_titles * (1 - found_share)
    return per_call, calls, calls * per_call


def machine():
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    except (ValueError, OSError, AttributeError):
        ram = float("nan")
    wsl = "microsoft" in platform.release().lower()
    return (f"{platform.system()} {platform.release()}{' (WSL)' if wsl else ''}, {os.cpu_count()} CPUs, "
            f"{ram:.1f} GB RAM, Python {platform.python_version()}, pandas {pd.__version__}")


def write_markdown(results, checks, estimate, spec, stages):
    r = results.set_index("titles")
    per_call, calls, est = estimate
    lines = [
        "# Cached rerun time report", "",
        "## Target", "",
        f"- A cached rerun of `python run_pipeline.py` (stages 1 to 7) finishes within **{config.TIME_BUDGET_SECONDS} s at 500 titles** (ADR).",
        f"- Headroom rule, set before measuring: median at 500 titles at most **{config.TIME_HEADROOM_SECONDS} s**, so a laptop twice as slow still meets the target.",
        f"- Scale rule, set before measuring: seconds per title at 5,000 at most **{config.LINEAR_TOLERANCE}x** the value at 500.", "",
        "## Method", "",
        f"- Machine: {spec}.",
        "- Timed: wall clock of the whole command, from start to exit, including Python start-up and imports; `--skip-spotcheck` because the spot-check is a live network step.",
        f"- Runs: {config.TIMING_RUNS} per size, all warm (files cached by the operating system). Run 1 is reported separately; median and maximum are over runs 2 onward.",
        "- Data: 112 = the real cached list. 500 and 5,000 = synthetic lists built in a temporary folder from the cached films, with ids, credit ids, IMDb ids, titles, collection and person ids rewritten, plus planted blanks, repeats, not-found ids, zero revenues and unreleased films. Synthetic results are discarded.",
        "- No network: every run uses a dummy API key, so a live call would fail; cache hits return before the polite sleep (fetch.py).",
        "- Reproduce: `python -m pipeline.timing`.", "",
        "## Results", "",
        "| Scenario | Runs | Run 1 (s) | Median (s) | Max (s) | Seconds per title | Target met? |",
        "|---|---|---|---|---|---|---|"]
    for n, row in r.iterrows():
        met = "yes" if row["median_s"] <= config.TIME_BUDGET_SECONDS else "no"
        lines.append(f"| {n:,} titles | {config.TIMING_RUNS} | {row['run1_s']:.2f} | {row['median_s']:.2f} | "
                     f"{row['max_s']:.2f} | {row['seconds_per_title']:.4f} | {met if n == 500 else 'n/a'} |")
    ratio = r.loc[5000, "seconds_per_title"] / r.loc[500, "seconds_per_title"]
    lines += ["",
              f"- Headroom at 500 titles: median {r.loc[500, 'median_s']:.2f} s against {config.TIME_HEADROOM_SECONDS} s: "
              f"**{'met' if r.loc[500, 'median_s'] <= config.TIME_HEADROOM_SECONDS else 'not met'}**.",
              f"- Scale: seconds per title at 5,000 is **{ratio:.2f}x** the value at 500 (rule: at most {config.LINEAR_TOLERANCE}x): "
              f"**{'met' if ratio <= config.LINEAR_TOLERANCE else 'not met'}**.", "",
              "| Correctness check | 112 | 500 | 5,000 |", "|---|---|---|---|"]
    for key in checks[500]:
        lines.append(f"| {key} | " + " | ".join(str(checks[n][key]) for n in [112, 500, 5000]) + " |")
    per_stage = pd.DataFrame(stages)
    lines += ["", "Per stage, last run (seconds, computation only; diagnosis, not the headline):", "",
              "| Stage | 112 | 500 | 5,000 |", "|---|---|---|---|"]
    for stage, row in per_stage.iterrows():
        lines.append(f"| {stage} | " + " | ".join(f"{row[n]:.2f}" for n in [112, 500, 5000]) + " |")
    lines += ["", "## Before / after", "", "No optimisation was needed or made; the code is measured as built.", "",
              "## Caveats", "",
              f"- First fetch is not timed. Estimated from the real fetch: {per_call:.2f} s per live call x about {calls:,.0f} calls "
              f"at 500 titles = about **{est / 60:.1f} minutes**, once; retries after a rate limit would add to this.",
              "- Adjoa's laptop is unknown; the headroom rule covers a machine about twice as slow. Running under WSL on the Linux file system is faster than on Windows paths.",
              "- Synthetic copies test volume, not new kinds of data problems that a real 500-title list may contain."]
    (config.PROJECT_ROOT / "timing_report.md").write_text("\n".join(lines) + "\n")


def main():
    spec = machine()
    rows, checks, stages = [], {}, {}
    with tempfile.TemporaryDirectory(prefix="streamvault-timing-") as tmp:
        tmp = Path(tmp)
        for n in [112, *config.TIMING_SIZES]:
            data_dir = config.DATA_DIR if n == 112 else tmp / f"data_{n}"
            n_rows = len(pd.read_csv(config.ID_LIST_PATH, dtype=str, keep_default_na=False, skip_blank_lines=False)) \
                if n == 112 else build_synthetic(n, data_dir)
            times = []
            for run in range(config.TIMING_RUNS):
                out_dir = tmp / f"out_{n}_{run}"
                seconds, stdout = run_once(data_dir, out_dir)
                times.append(seconds)
                if run < config.TIMING_RUNS - 1:
                    shutil.rmtree(out_dir)                                # keep only the last run's outputs
            checks[n] = check_correctness(stdout, out_dir)
            stages[n] = pd.read_csv(out_dir / "stage_timings.csv").set_index("stage")["seconds"]
            later = times[1:]
            rows.append({"titles": n, "rows_in_list": n_rows, "run1_s": times[0],
                         "median_s": statistics.median(later), "max_s": max(later),
                         "seconds_per_title": statistics.median(later) / n_rows})
            print(f"[8 timing] {n:>5} titles: median {statistics.median(later):.2f} s | max {max(later):.2f} s | {checks[n]}")
            if n != 112:
                shutil.rmtree(data_dir)                                   # free disk before the next size
    results = pd.DataFrame(rows)
    results.to_csv(config.OUTPUT_DIR / "timing_report.csv", index=False)
    write_markdown(results, checks, first_fetch_estimate(500), spec, stages)
    print("-> outputs/timing_report.csv, timing_report.md")


if __name__ == "__main__":
    main()