# ADR-004: Measure performance as box office per film, median first, with a fixed rule for declaring a winner

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

The brief does not say what "performs better" means. The data has box office, budget and audience rating, but no licence prices and no streaming viewing. Box office is stated in the money of its day. The standalone side is small (8 films from 2000) and one film is 29.6% of its box office. These rules were fixed before any result was viewed.

## Decision

Performance is worldwide box office per film, standing in for audience demand. The headline is the median (the middle film), with the mean beside it. Periods are all years and release year 2000 or later. No inflation adjustment is made. A side wins only if both sides have at least 5 independent units (collections for franchises) and it wins on the median, on the mean, and with each side's top film removed; otherwise "no clear winner", and a disagreement between periods is printed as a warning.

## Alternatives considered

### Alternative A: Return on budget (box office divided by budget)

- **How it would work:** rank by how many times a film earned its budget.
- **Why it is attractive:** rewards efficient films.
- **Why rejected:** it measures the studio's return on money StreamVault never pays; a licence buys audience, not production efficiency.
- **Recommendation under it:** unchanged: franchise films earned 5.6 times their budget against 3.8 for standalones (all years), and 5.1 against 3.8 from 2000.

### Alternative B: Audience rating

- **How it would work:** rank by average TMDb rating.
- **Why it is attractive:** reflects how much viewers liked a film.
- **Why rejected:** ratings drift daily (two changed within a day) and say little about how many people watch.
- **Recommendation under it:** **reverses**: standalones are rated higher, 8.44 against 7.6 (all years) and 8.19 against 7.45 from 2000. On audience appreciation rather than audience size, standalones win. The standalones on this list are mostly acclaimed classics, which partly explains it. Rejected as the main measure because a licence pays for viewers, not ratings, but stated in the memo so Kwame hears it from us first.

### Alternative C: Mean instead of median

- **How it would work:** use the average film.
- **Why it is attractive:** familiar.
- **Why rejected:** one film (Inception) moves the standalone mean by a wide margin.
- **Recommendation under it:** unchanged: franchise wins on the mean in both periods.

### Alternative D: Adjust for inflation

- **How it would work:** convert all box office to today's money.
- **Why it is attractive:** answers Finance's objection directly.
- **Why rejected:** no inflation index is in scope; the 2000-onward period limits the era gap instead.
- **Recommendation under it:** not computed; from 2000 the two groups are almost the same age (2007 vs 2006) and franchise still leads 2.8x.

## Consequences

- **What this buys:** a verdict that cannot be produced by one film or one choice of average; the same rule in both periods.
- **What this costs:** box office is a proxy: it measures cinema demand, not streaming viewing or value for money.
- **What it costs the client if I am wrong:** if licence prices rise faster than audience size, a bigger audience does not mean a better buy.
- **What would make me revisit this:** licence prices or streaming viewing data become available.

## What this survives

A 500-title list: the rule recomputes in both periods and still prints a warning if they disagree. With more standalones, the small-group caveat may no longer apply.
