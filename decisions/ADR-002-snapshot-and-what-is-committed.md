# ADR-002: Analyse a cached snapshot; commit neither the raw responses nor the outputs; commit a small reference result

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

The analysis needs about 230 calls to a free, shared API, and Adjoa reruns it every quarter, sometimes live in a meeting. TMDb values drift (two ratings changed within a day). The repository is public. TMDb's terms allow caching to provide a service, with attribution, but do not clearly allow publishing its full responses. A clean clone must run with no manual edits.

## Decision

Every raw response is cached once in a local data folder and the analysis reads that snapshot, with its fetch dates recorded. The cached responses and the outputs are not committed; both are rebuilt from code. A small reference result (verdicts, shortlists, deal note, box office per film, the id-list fingerprint and fetch dates) is committed, so a fresh run can be compared with it and any drift is reported.

## Alternatives considered

### Alternative A: Commit the cached responses

- **How it would work:** the clean clone runs offline against our exact snapshot.
- **Why it is attractive:** reproduces the memo exactly, with no key needed.
- **Why rejected:** publishes TMDb's full responses in a public repository, which their terms may not allow.
- **Recommendation under it:** unchanged.

### Alternative B: Commit nothing

- **How it would work:** the clean clone fetches live and produces its own outputs.
- **Why it is attractive:** no data in the repository at all.
- **Why rejected:** nobody could tell whether a fresh run's numbers drifted from the memo's.
- **Recommendation under it:** unchanged.

### Alternative C: Always fetch live, no cache

- **How it would work:** every run calls the API.
- **Why it is attractive:** always current.
- **Why rejected:** about 230 calls per rerun, slower in a meeting, and two runs a minute apart could differ.
- **Recommendation under it:** unchanged, but not reproducible.

## Consequences

- **What this buys:** identical reruns from the same cache (verified: two reruns gave byte-identical outputs); no raw TMDb data published; drift against the memo is reported, not guessed.
- **What this costs:** a clean clone needs a TMDb key and about two minutes for the first fetch, and its numbers can differ slightly from the memo's.
- **What it costs the client if I am wrong:** if TMDb's terms do allow publishing, offline reproduction was given up for nothing.
- **What would make me revisit this:** written permission from TMDb, or a private repository.

## What this survives

A 500-title list: the cache simply grows; the first fetch takes about 7 to 8 minutes, once. The comparison against the last saved result tells Adjoa what changed between quarters.
