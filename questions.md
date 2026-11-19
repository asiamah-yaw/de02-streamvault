# Questions for the client

Findings the data cannot settle. The engineer decides how to handle data; the business decides what it means. Each row shows the default applied and its cost if wrong, so it can be answered in one reply. Ordered by risk at the end.

| ID | To | Finding | Question | Status | Default applied | Cost if wrong | ADR |
|---|---|---|---|---|---|---|---|
| Q1 | Kwame | F-10 (franchise definition) | We treat a film as a franchise entry when TMDb lists it in a collection. Some franchise entries have no collection on TMDb (The Good, the Bad and the Ugly is one). Is "in a TMDb collection" an acceptable definition of a franchise for this decision? | Kwame unavailable | Franchise = in a TMDb collection; standalone = no collection; known exceptions named | Franchise entries without a collection count as standalones and shift both groups' figures | planned |
| Q2 | Adjoa | F-02 | Five ids (8471293, 8471294, 9412887, 9412888, 7733901) are not on TMDb. Do they appear in your evaluation tracker with titles? If so, the correct ids can replace them. | Open | Excluded and counted as "not found" | Up to 5 intended films are missing from the analysis | n/a |
| Q3 | Adjoa | F-01, F-07 | Row 94 holds "tt0468569", an IMDb-style id. Which film was intended? | Closed: answered by the data. It is The Dark Knight (TMDb 155), already on the list | Treated as a repeat of 155 | None | n/a |
| Q4 | Adjoa | F-08 | Which films does each studio's bundle include? 9 of 32 franchises have only one film on the list. | Open | A bundle is treated as the films on the list | Franchise figures may miss weak entries and look better than the real bundle | planned |
| Q5 | Kwame | (memo) | Which five-film bundle did the competitor license last quarter? | Kwame unavailable | Not assessed | Whether passing on it was right stays unanswered | n/a |