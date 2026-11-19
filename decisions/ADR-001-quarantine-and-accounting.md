# ADR-001: Quarantine unusable rows with a reason, and let the API decide which ids exist

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

The candidate list was built from three sources over four years and never cleaned. It holds 127 rows, including a blank, "N/A", "-1", an IMDb-style id and six repeated ids. Five more ids look valid but TMDb does not recognise them. The brief requires every id to be accounted for and the totals to reconcile.

## Decision

Every row is classified by fixed rules; unusable and repeated rows go to a quarantine file with their row number and reason, and nothing is deleted. Ids that pass are fetched once; whether a film exists is decided by TMDb's answer (a "not found" is recorded), not by a guessed id limit. The IMDb-style id is quarantined and then looked up among the fetched films.

## Alternatives considered

### Alternative A: Drop bad rows silently

- **How it would work:** filter them out on load.
- **Why it is attractive:** simplest code.
- **Why rejected:** Kwame would see 112 films with no account of the other 15.
- **Recommendation under it:** unchanged (the same 112 films).

### Alternative B: Reject ids above a size limit

- **How it would work:** treat very large ids as invalid before fetching.
- **Why it is attractive:** saves five calls.
- **Why rejected:** any limit is a guess and would break when TMDb's ids grow; the API's answer is evidence.
- **Recommendation under it:** unchanged.

### Alternative C: Resolve the IMDb id through TMDb's search-by-external-id endpoint

- **How it would work:** one extra call to translate tt0468569 to a TMDb id.
- **Why it is attractive:** resolves the row directly.
- **Why rejected:** the brief allows the details and credits endpoints only; the fetched films already carry IMDb ids, which proved it is The Dark Knight (155).
- **Recommendation under it:** unchanged (it would return a film already on the list).

## Consequences

- **What this buys:** 127 = 112 analysed + 7 repeats + 3 unusable + 5 not found, reconciled by assertion on every run.
- **What this costs:** a quarantine file and a manifest to read.
- **What it costs the client if I am wrong:** if a not-found id was a real film under a typo, it is missing from the shortlist (question Q2).
- **What would make me revisit this:** Adjoa identifies the five unknown ids, or the brief allows another endpoint.

## What this survives

A 500-title list with new kinds of bad rows: the rules classify them generically and the counts still reconcile. New unknown ids are listed automatically for Adjoa to identify.
