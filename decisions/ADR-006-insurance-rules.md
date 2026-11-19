# ADR-006: Keep the zero and unreleased rules as insurance, and run them before positions are counted

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Yaw Omari Asiamah

## Context

On TMDb a zero budget or box office usually means "not entered", and unreleased films have no fair box office. In this list no film has a zero, none is unreleased and none is dated after the fetch. The rubric penalises a fix applied to nothing broken.

## Decision

The rules stay, labelled as insurance: a zero or negative budget or box office becomes missing, and unreleased or future-dated films are excluded with a reason. They run before the franchise label and the first/middle/last positions are worked out, so an excluded film never changes its neighbours' labels. Their effect today (0 rows) is reported, not claimed as a fix.

## Alternatives considered

### Alternative A: Remove the rules, since nothing triggers them

- **How it would work:** no handling for zeros or unreleased films.
- **Why it is attractive:** no code that does nothing today.
- **Why rejected:** next year's 500 titles may contain them, and Adjoa would get wrong medians with no warning.
- **Recommendation under it:** unchanged today.

### Alternative B: Treat a zero as a real flop

- **How it would work:** keep zeros in the averages.
- **Why it is attractive:** no assumption about what a zero means.
- **Why rejected:** a missing figure would drag its group down as if the film earned nothing.
- **Recommendation under it:** unchanged today (no zeros).

## Consequences

- **What this buys:** protection for next year's list, proven to work (the timing test planted zeros and unreleased films; the rules caught all of them).
- **What this costs:** code that changes nothing this year.
- **What it costs the client if I am wrong:** if a real flop is entered as zero, it is treated as unknown instead of as a failure.
- **What would make me revisit this:** a zero that turns out to be a real figure.

## What this survives

A 500-title list: this is the point of the rules; the cleaning report counts every row they change.
