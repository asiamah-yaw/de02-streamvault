# Questions for the client

Findings the data cannot settle. The engineer decides how to handle data; the business decides what it means. Each row shows the default applied and its cost if wrong, so it can be answered in one reply. Ordered by risk at the end.

| ID | To | Finding | Question | Status | Default applied | Cost if wrong | ADR |
|---|---|---|---|---|---|---|---|
| Q1 | Kwame | F-0? (franchise definition) | We treat a film as a franchise entry when TMDb lists it in a collection. Some sequels have no collection on TMDb. Is "in a TMDb collection" an acceptable definition of a franchise for this decision? | Kwame unavailable | Franchise = in a TMDb collection; standalone = no collection | Sequels without a collection count as standalones and shift both groups' figures | planned |
| Q2 | Adjoa | F-02 | Five ids (8471293, 8471294, 9412887, 9412888, 7733901) are not on TMDb. Do they appear in your evaluation tracker with titles? If so, the correct ids can replace them. | Open | Excluded and counted as "not found" | Up to 5 intended films are missing from the analysis | n/a |
| Q3 | Adjoa | F-01 | Row 94 holds "tt0468569", an IMDb-style id. Which film was intended? | Open | Excluded (IMDb id, outside the brief's endpoints); checked against fetched films in profiling | One intended film may be missing | planned |