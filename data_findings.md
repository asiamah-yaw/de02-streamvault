## Summary
(written at the end, once all findings are ranked)

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---|---|---|
| Rows in id_list.csv | 127 | | client input, read as text with blank rows kept |
| Unusable rows quarantined | 124 | −3 | 1 blank (row 68), 1 not a number "N/A" (row 110), 1 non-positive "-1" (row 29) |
| Repeated ids quarantined | 118 | −6 | the same TMDb id listed again: 155, 278, 550, 603, 680, 1891 |
| IMDb-format id quarantined | 117 fetchable | −1 | tt0468569 (row 94), verified in profiling as The Dark Knight (155), already on the list |
| After fetching from TMDb | 112 found | −5 | 5 ids returned "not found" (404): 8471293, 8471294, 9412887, 9412888, 7733901 |
| Films analysed | 112 | | 96 in a TMDb collection, 16 not |

## Findings, ranked by risk
(ranked at the end; severities are provisional)

### F-01: The candidate list contains rows that are not usable TMDb ids — Severity: (to be ranked)

- **What it is:** 10 of the 127 rows cannot be sent to the API as they are: a blank row (row 68), the text "N/A" (row 110), "-1" (row 29), an IMDb-style id "tt0468569" (row 94), and 6 ids listed twice (155, 278, 550, 603, 680, 1891). Profiling showed that tt0468569 is The Dark Knight, already on the list as 155 (see F-07), so only 3 rows are truly unusable and 7 are repeats.
- **How I detected it:** I read the file as text with blank rows kept, then classified every row with fixed rules. The result is in outputs/quarantine.csv.
- **Scale:** 10 of 127 rows (7.9%): 3 unusable, 7 repeats. 117 unique ids remain to fetch.
- **Effect on the client's number:** If invalid and duplicate IDs were allowed through, extraction would include failed API requests and the same film could be counted multiple times. This would affect the franchise-versus-standalone analysis by distorting counts and averages. After classification and deduplication, only unique fetchable movie IDs proceed to extraction.
- **What I did about it:** I quarantined each row with its reason and row number. Repeated ids are fetched once, and nothing is deleted.
- **Residual risk:** A fetchable ID may still fail validation when checked against TMDb, because format validation does not guarantee the film exists. These cases are handled in Stage 2 (see F-02). The same film could also appear under two different IDs; profiling checked repeated IMDb ids and repeated titles and found none. What the 3 unusable rows were meant to be is unknown.

### F-02: Five candidate ids do not exist on TMDb — Severity: (to be ranked)

- **What it is:** 5 ids that looked valid (8471293, 8471294, 9412887, 9412888, 7733901) returned "not found" from TMDb. They are far larger than every other id in the list (the rest are at most about 301,528).
- **How I detected it:** the fetch stage requested each id once; TMDb answered 404 for these five. Recorded in outputs/fetch_manifest.csv.
- **Scale:** 5 of 117 fetchable ids (4.3%); 112 films go forward.
- **Effect on the client's number:** If these IDs had been silently dropped, Kwame would have no record that they were supplied but could not be matched to a TMDb film. This would make the final film count appear lower without explanation and could lead to questions about whether records were lost during processing. By recording them as "not found", the difference between the input count (117 fetchable IDs) and the analysis set (112 films) can be fully reconciled. If any of the five IDs were intended to represent valid films, their exclusion could also slightly reduce coverage of the client's catalogue.
- **What I did about it:** recorded each as "not found" with the fetch time; credits were not requested for them; they are excluded from the analysis but counted in the reconciliation.
- **Residual risk:** The underlying cause of these invalid IDs could not be verified. They may be typographical errors, IDs copied from a different film database, or incorrectly mapped records from one of the source files. If the IDs were intended to represent real films, those films will not appear in the final analysis until the correct identifiers are obtained. Further investigation with the data provider would be required to determine the original intended records.

### F-03: Talent counts may reflect franchises, not people — Severity: High (talent ask)

- **What it is:** Many directors and lead actors appear on several films, often within one franchise, so "appears often" can mean "worked on a franchise" rather than "picks good films".
- **How I detected it:** Stage 4 counts of distinct films per person (outputs/join_report.csv). The co-directed films point the same way: most are franchise entries (The Matrix ×3, Avengers ×2, Shrek ×2, Pirates of the Caribbean).
- **Scale:** 13 of 66 directors and 19 of 48 lead actors have 3 or more films.
- **Effect on the client's number:** A person can look reliable only because their franchise did well. Kwame's negotiators would then credit that person with the franchise's results and press a point the evidence does not support. This affects the talent ask only; the franchise-versus-standalone comparison does not use these counts.
- **What I did about it:** Stage 7 counts each person's standalone films separately and reports distinct collections per person. The minimum film count is set in Phase 7 and recorded in an ADR before any talent results are viewed.
- **Residual risk:** With 112 films, few people may reach the minimum on standalone titles alone. If so, the talent answer is reported as "could not verify" and is not stated more firmly than the data allows.

### F-04: Co-Director credits are not counted as directors — Severity: Low

- **What it is:** TMDb lists some people as "Co-Director", a separate job from "Director". The analysis counts only "Director".
- **How I detected it:** The Directing job counts (outputs/director_job_counts.csv), and a check that none of those people is also credited as Director on the same film.
- **Scale:** 7 Co-Director credits on 5 animated films (Ice Age, Ice Age: Dawn of the Dinosaurs, Monsters, Inc., Shrek the Third, Toy Story 2).
- **Effect on the client's number:** These 7 people are left out of the director ranking. Every film still has a Director credit, so no film is lost and the film counts do not change.
- **What I did about it:** The decision is an exact match on "Director". Adding "Co-Director" is a one-line change to `DIRECTOR_JOBS` in config, so the memo can state whether the answer changes under the alternative.
- **Residual risk:** Low. Only someone near the minimum film count could change rank; Lee Unkrich, with 2 Co-Director credits, is the one known case.

### F-05: The standalone side of the comparison is small — Severity: High

- **What it is:** Only 16 of 112 films are outside a collection, and only 8 from 2000 onward.
- **How I detected it:** Stage 5 group sizes, outputs/quality_report.csv (check "films").
- **Scale:** All years: 96 in a collection vs 16 not. From 2000: 63 vs 8.
- **Effect on the client's number:** The standalone average from 2000 rests on 8 films, so one film more or less can move it noticeably. The window Yaw trusts is the one with the least evidence.
- **What I did about it:** Group sizes are reported next to every average; no claim of statistical significance is made.
- **Residual risk:** Any standalone-versus-franchise conclusion from 2000 is directional only.

### F-06: One film drives the standalone average — Severity: High

- **What it is:** Standalone revenue is uneven; collection revenue is not.
- **How I detected it:** Stage 5 skew table, outputs/quality_skew.csv.
- **Scale:** From 2000, standalone mean 354M vs median 283M; Inception alone is 29.6% of the group's revenue. Collection films: mean 793M vs median 787M, top film 5.9%.
- **Effect on the client's number:** Using the mean flatters standalones by Inception's result; the median is less affected. The choice of measure can change the size of the gap.
- **What I did about it:** Mean vs median is decided by ADR in Phase 7, and both are reported.
- **Residual risk:** With 8 films, even the median moves if one film is added or removed.

### F-07: The Dark Knight was entered three times — Severity: Low

- **What it is:** tt0468569 is the IMDb id of The Dark Knight, already on the list as TMDb id 155 (rows 1 and 90).
- **How I detected it:** Stage 5 looked up each quarantined IMDb-format value in the fetched films' IMDb ids (check "quarantined_imdb_id_found_in_films").
- **Scale:** 1 row (row 94).
- **Effect on the client's number:** None; the film is analysed once. It shows that the three source lists overlap and use different id systems.
- **What I did about it:** Row 94 is a verified repeat; unusable rows fall from 4 to 3.
- **Residual risk:** None for this row.

### F-08: Several franchises are represented by a single film — Severity: Medium

- **What it is:** 9 of 32 collections have only one film in the candidate list.
- **How I detected it:** Stage 5, check "collections_with_one_film_in_list".
- **Scale:** 9 of 32 collections.
- **Effect on the client's number:** Franchise figures describe the films listed, not the bundle the studio sells. A bundle's weak entries may be missing from the list, which would flatter franchises.
- **What I did about it:** Reported; bundle-level views use only collections with two or more films.
- **Residual risk:** Bundle completeness cannot be checked with the allowed data (see Could not verify).

### F-09: More than a third of the films predate 2000, and revenue is not inflation-adjusted — Severity: Medium

- **What it is:** 41 of 112 films were released before 2000. TMDb revenue is stated in the money of its day (an assumption about the field; the API does not say).
- **How I detected it:** Stage 5, check "films_before_cutoff".
- **Scale:** 41 of 112 films.
- **Effect on the client's number:** Older films look smaller than they were, so the all-years comparison mixes values that are not comparable. This is Yaw's objection, and it is fair.
- **What I did about it:** Every comparison is shown for all years and from 2000; no inflation adjustment is made because no index is in scope.
- **Residual risk:** If the two windows disagree, the 2000-onward result is the one to defend.

### F-10: A known franchise entry has no TMDb collection — Severity: Low

- **What it is:** The Good, the Bad and the Ugly (1966) is the third film of a trilogy but has no collection in TMDb, so the rule "no collection = standalone" labels it standalone.
- **How I detected it:** Reading the 16 no-collection titles; the sequel title pattern found 0.
- **Scale:** 1 of 16 standalones, all-years window only.
- **Effect on the client's number:** One older, low-revenue franchise entry sits in the standalone group.
- **What I did about it:** Tested both ways in Phase 6; the rule stays, with this film named as the known exception.
- **Residual risk:** At 500 titles the list cannot be read by eye; the review list is the safeguard.

### F-11: Entry position describes the listed films, not the series — Severity: Medium

- **What it is:** Each franchise film is labelled first, middle or last by release date among the films of its collection that are on the list. The full size of a series is not in the allowed data.
- **How I detected it:** Stage 6 position counts, outputs/cleaning_report.csv.
- **Scale:** 41 middle films in 22 collections; 23 first, 23 last, 9 only listed, 16 standalone.
- **Effect on the client's number:** The "weak middle entries" test is exact where the whole series is listed (Harry Potter, 8 of 8) and approximate where it is not: a film labelled "first" may be the second entry of the series.
- **What I did about it:** The label is named "position among listed films" in the code and the decision note; the test is reported only for collections with 3 or more listed films.
- **Residual risk:** Labels change when next year's list adds earlier or later films; Adjoa's rerun note says so.

### F-12: The cleaning rules for zeros and unreleased films change nothing in this list — Severity: Low

- **What it is:** No film has a zero or missing budget or revenue, none is unreleased, and none is dated after the fetch.
- **How I detected it:** Stage 6 cleaning report: 0 rows affected for each of these rules.
- **Scale:** 0 of 112 films.
- **Effect on the client's number:** None today.
- **What I did about it:** The rules stay as insurance for next year's list, labelled as such, and are proven by a test with made-up rows.
- **Residual risk:** None for this list.

### F-13: One film universe can appear as two collections — Severity: Medium (talent ask)

- **What it is:** TMDb lists Iron Man and The Avengers as separate collections, although they belong to one connected film series. The talent rule counts them as two independent contexts.
- **How I detected it:** Reading the qualifying talent in outputs/talent_leads.csv: Robert Downey Jr. reaches 2 contexts only through these two collections.
- **Scale:** 1 lead actor in the qualifying list; other shared universes may exist and cannot be detected from the allowed data.
- **Effect on the client's number:** Robert Downey Jr. looks like a signal across contexts when the evidence is one franchise. Negotiators should not use him as a lever outside that series.
- **What I did about it:** Reported; the memo treats his figure as franchise evidence only.
- **Residual risk:** The same effect can appear with other connected series next year; the talent table shows collections and standalone films so a reader can check.


## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| The file uses Windows line endings | It differs from the Linux files around it | It does not change any value, and it is stored unchanged in git (.gitattributes) |
| 9 films have two or more directors | It could look like repeated rows from the join | They are real co-directing credits (the Wachowskis, the Russos). The 122 Director credits equal 112 films plus 10 extra: one extra on each of 8 films and two on Shrek 2 (three directors), so the totals reconcile. The films table keeps one row per film, with the names in `director_names` and the count in `n_directors` |
| No film has a missing or zero budget or revenue | Zeros were expected on TMDb | All 112 have both values; the zero rule stays to protect next year's list but changes nothing today |
| Some budgets are very small (The Good, the Bad and the Ugly: $1.2M) | Could be values entered in millions | They match the era of the films; the 10 lowest are all real productions |
| Extreme revenue/budget ratios (Star Wars 70x, Jaws 67x) | Look like data errors | They are known breakout hits, not entry mistakes |

## Could not verify
- What the five "not found" ids (8471293, 8471294, 9412887, 9412888, 7733901) were meant to be; they may be typos or ids from another system.
- What the 3 unusable rows (blank, "N/A", "-1") were meant to be.
- Whether each franchise in the list is the complete bundle the studio sells (no collection data in scope).
- Revenue in today's money (no inflation index in scope).
- Which five-film bundle the competitor licensed, so whether passing on it was right.
- Results describe these candidates, which are mostly well-known hits, not films in general.