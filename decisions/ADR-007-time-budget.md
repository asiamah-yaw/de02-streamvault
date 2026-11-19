# ADR-007: A cached rerun of 500 titles finishes within 10 seconds

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

The rubric asks for results inside the client's time budget, measured. The brief gives no number, only that Adjoa reruns on her own laptop, sometimes live in a meeting, and that next year's list is about 500 titles. The budget and the rules for judging it were set before measuring.

## Decision

A rerun from the cache (stages 1 to 7, the whole command including start-up) must finish within 10 seconds at 500 titles, with a median of at most 5 seconds as headroom for a slower laptop, and cost per title at 5,000 titles at most 1.5 times that at 500. The first fetch and the live check are excluded, because they depend on the network, and the first fetch is estimated separately.

## Alternatives considered

### Alternative A: Include the first fetch in the budget

- **How it would work:** time a run that downloads everything.
- **Why it is attractive:** the full experience of a new list.
- **Why rejected:** network-bound and done once, before a meeting, not in it; measuring it would mean hammering a free API.
- **Recommendation under it:** cannot move it.

### Alternative B: A looser budget (60 seconds)

- **How it would work:** any rerun under a minute passes.
- **Why it is attractive:** easy to meet.
- **Why rejected:** a minute is too long for a room waiting on a number.
- **Recommendation under it:** cannot move it.

### Alternative C: Optimise the slowest stage now

- **How it would work:** speed up reading and reshaping the cached files.
- **Why it is attractive:** more headroom.
- **Why rejected:** the target is met with room to spare.
- **Recommendation under it:** cannot move it.

## Consequences

- **What this buys:** measured on a 4-CPU laptop under WSL: 1.58 s for this year's list, 3.40 s at 500 titles, 29.74 s at 5,000. Cost per title at 5,000 is 0.87 times that at 500. Every run made 0 live calls and reconciled every row.
- **What this costs:** a separate timing command and a temporary 0.5 GB of synthetic data while it runs.
- **What it costs the client if I am wrong:** on a much slower laptop a 500-title rerun could approach 10 seconds.
- **What would make me revisit this:** the list passes about 1,700 titles, where the measured 0.0059 s per title reaches 10 seconds. Reading and reshaping the cached files is 79% of the time at 5,000 titles, so that is where to start.

## What this survives

A 500-title list: measured directly at 3.4 seconds. The first fetch of a new 500-title list is estimated at about 7 to 8 minutes, once.
