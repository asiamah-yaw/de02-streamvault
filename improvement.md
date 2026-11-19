# Improvement beyond the brief: a run-to-run change report

## The problem it solves

Adjoa reruns this analysis every quarter, sometimes live in a meeting, and the first question in the room will be: *what changed since last time, and why?* A different shortlist can come from three places: new or removed titles on the candidate list, TMDb revising its figures, or a change to the analysis settings or code. Each run writes 32 output files; without help, Adjoa would have to compare them by hand and could not tell which of the three caused a change.

## What I built

One command that compares the current run with the last saved result and prints a short report (also written to `outputs/change_report.md`). Measured: it takes about half a second.

```bash
python -m pipeline.compare_runs            # compare this run with the latest saved result
python -m pipeline.compare_runs --save     # save this run as the starting point for next quarter
python -m pipeline.compare_runs --demo     # show the report on a made-up previous quarter
```

The report answers four things, in the order they are asked in the room:

1. **Where a change came from:** fingerprints of the candidate list (the sorted, de-duplicated ids, so re-sorting the file is not a change), of the settings file and of the analysis code, plus the dates the TMDb data was fetched.
2. **The decision:** the verdict in each time period (in bold, with a warning, if it changed), the franchise lead, and the strongest franchise's demand index, the number the deal note rests on.
3. **The shortlist and deal note:** the strongest franchise, its lead over the second, and any franchise or standalone pick that came in or dropped out.
4. **The films:** titles added or removed, any film whose franchise label changed, and box-office revisions of 1% or more (smaller ones are ignored), largest first.

When nothing has changed it says so in one line. A saved result is a small dated folder in `snapshots/` and is never overwritten. The 19 November 2026 result is committed as the reference, so a fresh clone can compare its own run with the figures in the memo and see any drift straight away.

**Box office can only change if the TMDb data was fetched again.** The pipeline reuses saved responses, so a quarterly rerun must first archive the old ones (README, "Rerunning next quarter"); the fetch dates in the first table show whether that happened.

**Demonstration.** Comparing the real run with the committed reference reports "No change at all", as it should. To show every part of the report working, `--demo` builds a made-up previous quarter from this run with one change of each kind. Its output, unedited:

```
(Demo: the previous quarter is made up from this run. It had 3 fewer titles (The Good, the Bad and the Ugly, The Shawshank Redemption, Requiem for a Dream), an earlier fetch in which Avengers: Endgame was 10% lower, The Departed in place of Inception, and no clear winner from 2000.)

# What changed: made-up previous quarter -> this run

## Where a change could come from

| | Previous | Current | Changed? |
|---|---|---|---|
| Candidate list (fingerprint of the ids) | previous-list | 82b0566f83ea | **yes** |
| Rows in the list | 124 | 127 | **yes** |
| Films analysed | 109 | 112 | **yes** |
| TMDb data fetched from | 2026-08-15 | 2026-11-19 | **yes** |
| TMDb data fetched to | 2026-08-15 | 2026-11-19 | **yes** |
| Settings (fingerprint) | 113fdff7ddfd | 113fdff7ddfd | no |
| Analysis code (fingerprint) | 52dd8c63f90a | 52dd8c63f90a | no |

Reading: the candidate list changed; the TMDb data was fetched at a different time.

## The decision

| Period | Verdict (previous -> current) | Franchise lead | Strongest franchise's demand index |
|---|---|---|---|
| all_years | franchise | 3.6x -> 3.6x | 3.6x -> 3.6x |
| from_2000 | no clear winner -> **franchise** | 1.2x -> 2.8x | 2.6x -> 2.6x |

**WARNING: the verdict changed in from_2000**

## The shortlist and the deal note

- Strongest franchise: The Avengers Collection
- Lead of the strongest franchise over the second: 1.77x -> 1.77x
- Franchise picks in: none; out: none
- Standalone picks in: Inception; out: The Departed

## Films

- Added: 3 (The Shawshank Redemption, The Good, the Bad and the Ugly, Requiem for a Dream)
- Removed: 0
- Franchise label changed: 0
- Box office revised by 1% or more: 1
  - Avengers: Endgame: 2,648M -> 2,943M
```

A test also compares two small invented results with a known verdict change, a removed film and a revised figure, and checks that the report names each one (`tests/`).

**Alternative considered: a run summary with fingerprints only.** It would prove whether two runs are identical, but not *what* changed or *why*, which is the question Kwame and Adjoa actually face. The fingerprints are kept, inside the change report.

## What it is worth to Kwame and Adjoa

- **For Adjoa:** "what changed?" is answered in about half a second, in the meeting, instead of by comparing 32 files afterwards. The first table tells her whether to ask whoever supplied the list, to look at TMDb's revisions, or to check a change to the settings.
- **For Kwame:** a changed shortlist arrives with its reason. If a title drops out, he can see whether it left the list or was overtaken after a revision, which is what the board will ask. The deal note's figures (the demand index and the lead over the second franchise) are shown each time, so a weakening deal is visible before the negotiation.
- **For whoever checks this work:** a fresh clone, run against today's TMDb, can be compared with the committed 19 November result, so any difference from the memo's figures is reported rather than guessed.

## What it cost

- 204 lines of code, reading files the pipeline already writes; no new data and no extra calls to TMDb.
- Each saved result is a folder of six files, and it is committed. It holds box office per film for all 112 analysed titles, with TMDb named as the source. That is more than the memo shows (about ten titles), though far less than TMDb's full responses, which remain uncommitted (ADR-002). TMDb's terms, as quoted on TMDb's support forum (read 19 November 2026), allow caching "for reasonable periods in order to provide your service"; whether publishing these figures fits that, and which terms apply to StreamVault's commercial use, is for Adjoa to confirm with TMDb (question Q6).
- It compares decision-level results only. It does not explain *why* TMDb revised a figure, and it ignores revisions under 1%.