# ADR-003: A franchise is a film that TMDb places in a collection

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

The whole comparison depends on which films count as franchise entries. Kwame is unavailable to define it. TMDb groups films into collections, but some franchise entries have none (The Good, the Bad and the Ugly), and 9 collections appear with only one film on the list.

## Decision

A film is a franchise entry if TMDb lists it in a collection; otherwise it is a standalone. The rule uses the data alone, so it reruns unchanged. Known exceptions are named and tested as alternatives, not applied by default.

## Alternatives considered

### Alternative A: A franchise needs 2 or more films on the list

- **How it would work:** the 9 single-listed collection films become standalones.
- **Why it is attractive:** a film alone from its collection may be sold alone.
- **Why rejected:** whether studios sell them alone is unknown; it is reported beside the default instead.
- **Recommendation under it:** franchise still wins: 2.1x all years, 1.8x from 2000 (down from 3.6x and 2.8x).

### Alternative B: Add known exceptions by hand

- **How it would work:** force The Good, the Bad and the Ugly to franchise.
- **Why it is attractive:** labels a known trilogy correctly.
- **Why rejected:** builds outside knowledge into the code, and Adjoa would have to maintain the list.
- **Recommendation under it:** franchise still wins: 2.7x all years; from 2000 unchanged at 2.8x.

### Alternative C: Detect sequels from titles

- **How it would work:** numbers or "Part" in a title mark a franchise.
- **Why it is attractive:** catches sequels without a collection.
- **Why rejected:** found none of the 16 standalones, and misses subtitle sequels while flagging films like "Apollo 13"; kept as a review list.
- **Recommendation under it:** unchanged (0 films moved).

## Consequences

- **What this buys:** a definition anyone can rerun, with its effect measured.
- **What this costs:** at least one known mislabel (one 1966 film).
- **What it costs the client if I am wrong:** the size of the franchise lead is overstated by up to about 40%; its direction does not change.
- **What would make me revisit this:** Kwame defines franchise differently (question Q1), or studios confirm which single films are sold alone (Q4).

## What this survives

A 500-title list: the rule applies unchanged; new exceptions surface on the review list, and the alternatives are recomputed automatically.
