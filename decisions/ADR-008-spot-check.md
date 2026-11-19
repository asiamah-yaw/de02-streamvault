# ADR-008: Spot-check the riskiest films by rule; the analysis stays on the fetched snapshot

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

A pipeline that runs is not the same as one that is right. The output must be checked against the live source, and any difference classified and resolved. A free, shared API must not be hammered. All rules below were set before comparing.

## Decision

Films are chosen by rule, with tie-breaks, from four kinds of risk: the messiest parsing, the extremes, films affected by a decision (including the shortlist boundaries), and every id that was not found. Each field is compared three ways (our table, the cached response, the live response), so a parsing error and a change at the source are told apart. Fields must match exactly, except ratings (within 0.1). At most 50 live calls. The analysis stays on the snapshot; if a change at the source would alter the verdict, the strongest franchise or any shortlisted title, the cache is refreshed before the board.

## Alternatives considered

### Alternative A: A random sample

- **How it would work:** re-check five films chosen at random.
- **Why it is attractive:** an unbiased picture of the whole list.
- **Why rejected:** likely to pick easy films; the risk lies in a few rows.
- **Recommendation under it:** cannot move it.

### Alternative B: Re-check every film

- **How it would work:** about 230 live calls.
- **Why it is attractive:** complete coverage.
- **Why rejected:** abuses a shared free API for little gain.
- **Recommendation under it:** cannot move it.

### Alternative C: Replace cached values with live ones automatically

- **How it would work:** update the snapshot whenever the source changed.
- **Why it is attractive:** always current.
- **Why rejected:** reruns would stop being identical, and the memo's numbers would silently change.
- **Recommendation under it:** cannot move it today (no decision-relevant change).

## Consequences

- **What this buys:** 13 films and 5 not-found ids checked in 31 calls; 130 of 130 fields matched what was fetched; 128 of 130 matched the live source exactly and 2 ratings drifted within tolerance; nothing moved the recommendation; the strongest franchise leads the next by 1.77 times.
- **What this costs:** the check compares TMDb with itself, so it shows we reproduce TMDb, not that TMDb is right; 13 films chosen for risk are not the whole list.
- **What it costs the client if I am wrong:** a wrong TMDb figure would pass unnoticed.
- **What would make me revisit this:** a second, independent box-office source becomes available.

## What this survives

A 500-title list: the same rules pick the same kinds of film, within the same call budget; a timestamped evidence folder keeps every run's live responses.
