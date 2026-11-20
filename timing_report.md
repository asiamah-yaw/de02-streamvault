# Cached rerun time report

## Target

- A cached rerun of `python run_pipeline.py` (stages 1 to 7) finishes within **10 s at 500 titles** (ADR).
- Headroom rule, set before measuring: median at 500 titles at most **5 s**, so a laptop twice as slow still meets the target.
- Scale rule, set before measuring: seconds per title at 5,000 at most **1.5x** the value at 500.

## Method

- Machine: Linux 6.18.58.1-microsoft-standard-WSL2 (WSL), 4 CPUs, 12.5 GB RAM, Python 3.14.4, pandas 3.1.1.
- Timed: wall clock of the whole command, from start to exit, including Python start-up and imports; `--skip-spotcheck` because the spot-check is a live network step.
- Runs: 5 per size, all warm (files cached by the operating system). Run 1 is reported separately; median and maximum are over runs 2 onward.
- Data: 112 = the real cached list. 500 and 5,000 = synthetic lists built in a temporary folder from the cached films, with ids, credit ids, IMDb ids, titles, collection and person ids rewritten, plus planted blanks, repeats, not-found ids, zero revenues and unreleased films. Synthetic results are discarded.
- No network: every run uses a dummy API key, so a live call would fail; cache hits return before the polite sleep (fetch.py).
- Reproduce: `python -m pipeline.timing`.

## Results

| Scenario | Runs | Run 1 (s) | Median (s) | Max (s) | Seconds per title | Target met? |
|---|---|---|---|---|---|---|
| 112 titles | 5 | 1.78 | 1.58 | 1.64 | 0.0124 | applies at 500 |
| 500 titles | 5 | 3.50 | 3.40 | 3.80 | 0.0068 | yes |
| 5,000 titles | 5 | 29.02 | 29.74 | 31.28 | 0.0059 | applies at 500 |

- Headroom at 500 titles: median 3.40 s against 5 s: **met**.
- Scale: seconds per title at 5,000 is **0.87x** the value at 500 (rule: at most 1.5x): **met**.

| Correctness check | 112 | 500 | 5,000 |
|---|---|---|---|
| zero_live_calls | True | True | True |
| reached_stage_7 | True | True | True |
| rows_reconcile | True | True | True |
| zero_rule_fired | 0 | 7 | 96 |
| films_excluded | 0 | 4 | 50 |

Per stage, last run (seconds, computation only; diagnosis, not the headline):

| Stage | 112 | 500 | 5,000 |
|---|---|---|---|
| 1_load | 0.01 | 0.01 | 0.02 |
| 2_fetch | 0.01 | 0.02 | 0.35 |
| 3_flatten | 0.51 | 1.77 | 22.76 |
| 5_quality | 0.06 | 0.06 | 0.12 |
| 4_join | 0.04 | 0.07 | 0.43 |
| 6_clean | 0.01 | 0.02 | 0.04 |
| 7_kpis | 0.21 | 0.27 | 0.89 |
| total_in_process | 0.95 | 2.59 | 28.74 |

## Before / after

No optimisation was needed or made; the code is measured as built.

## Caveats

- First fetch is not timed here. Measured in a clean clone on 20 November 2026: 229 calls in 118 s (0.52 s per call). At 500 titles, about 1,000 calls = about **8 to 9 minutes**, once; retries after a rate limit would add to this.
- Adjoa's laptop is unknown; the headroom rule covers a machine about twice as slow. Running under WSL on the Linux file system is faster than on Windows paths.
- Synthetic copies test volume, not new kinds of data problems that a real 500-title list may contain.
