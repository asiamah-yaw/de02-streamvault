# Data findings — StreamVault

## Summary

The candidate list held 127 rows. **112 films were analysed**; the other 15 are accounted for below, and none of the gaps changes the recommendation. All data comes from TMDb, fetched on 2026-11-19 and re-checked live the same day.

| Where the 127 rows went | Rows | What the gap costs Kwame |
|---|---|---|
| Analysed | 112 | — |
| Repeats of a film already on the list (6 by TMDb id; 1 by IMDb id, The Dark Knight) | 7 | Nothing: each film is analysed once |
| Unusable entries (blank, "N/A", "-1") | 3 | Up to 3 intended titles unknown; nobody can say what they were |
| Ids TMDb does not recognise | 5 | Up to 5 intended titles not assessed (question Q2 to Adjoa) |
| Excluded after fetching (unreleased or dated after the fetch) | 0 | — |

**The problems that matter most** (ranked below) all concern *how much evidence* stands behind the comparison, not whether the data is wrong: the standalone side is small (8 films from 2000), one film drives its average, and 9 franchises are represented by a single film. Each was measured. Under every alternative tested, franchise films still out-earn standalones in both windows; what moves is the size of the gap (1.8 to 3.6 times), not its direction.

## Risk ranking (by measured effect on the recommendation)

| Rank | Finding | Severity | Measured effect on the franchise-versus-standalone gap (all years / from 2000) | Moves the verdict? |
|---|---|---|---|---|
| 1 | F-08 Single-film franchises | High | 3.6x / 2.8x falls to 2.1x / 1.8x if they count as standalones | No |
| 2 | F-05 Small standalone group | High | 16 / 8 standalone films; group sizes shown beside every figure | No (passes the minimum of 5) |
| 3 | F-06 One film drives the standalone average | High | Inception is 29.6% of standalone revenue from 2000; franchise still wins with it removed | No |
| 4 | F-03 Talent counts reflect franchises | High (talent ask) | Of 13 directors and 19 leads with 3+ films, one director's signal holds outside a single franchise | Talent ask only |
| 5 | F-09 Pre-2000 films, revenue not inflation-adjusted | Medium | Gap is 3.6x all years vs 2.8x from 2000; median release years 2007 vs 2006 from 2000 | No |
| 6 | F-10 A franchise entry with no collection | Medium | 3.6x falls to 2.7x all years; unchanged from 2000 | No |
| 7 | F-11 Position among listed films only | Medium | Middle-entry test is approximate where a series is partly listed | Middle-entry claim only |
| 8 | F-13 One film universe split into two collections | Medium (talent ask) | One lead actor's "two contexts" are one series | Talent ask only |
| 9 | F-02 Five ids not on TMDb | Medium | Unknown: up to 5 titles not assessed | Unknown |
| 10 | F-01 Unusable rows in the list | Low | 3 titles unknown; 7 repeats cost nothing | No |
| 11 | F-04 Co-Director credits not counted | Low | 7 people on 5 films left out of the director ranking | No |
| 12 | F-07 The Dark Knight entered three times | Low | None | No |
| 13 | F-12 Zero and unreleased rules change nothing | Low | 0 rows affected | No |
| 14 | F-14 Live re-check | Low | 130 of 130 fields reproduce what was fetched; nothing changed that moves the answer | No |

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---|---|---|
| Rows in id_list.csv | 127 | | client input, read as text with blank rows kept |
| Unusable rows quarantined | 124 | −3 | 1 blank (row 68), 1 not a number "N/A" (row 110), 1 non-positive "-1" (row 29) |
| Repeated ids quarantined | 118 | −6 | the same TMDb id listed again: 155, 278, 550, 603, 680, 1891 |
| IMDb-format id quarantined | 117 fetchable | −1 | tt0468569 (row 94), verified in profiling as The Dark Knight (155), already on the list |
| After fetching from TMDb | 112 found | −5 | 5 ids returned "not found" (404): 8471293, 8471294, 9412887, 9412888, 7733901 |
| After cleaning | 112 analysed | 0 | no film unreleased or dated after the fetch |
| Films analysed | 112 | | 96 in a TMDb collection, 16 not |

## Findings, ranked by risk

### F-08: Several franchises are represented by a single film — Severity: High

- **What it is:** 9 of 32 collections have only one film on the candidate list. Under the default rule these films count as franchise, although a studio may sell such a film on its own.
- **How I detected it:** Stage 5, check "collections_with_one_film_in_list"; effect measured in stage 7 (outputs/kpi_sensitivity.csv, scenario "franchise_needs_2plus_listed").
- **Scale:** 9 of 32 collections; 9 of 96 franchise films (The Silence of the Lambs, The Smurfs, Jaws, Monsters, Inc., Ghostbusters, Mad Max: Fury Road, Blade Runner, The Lion King, The Incredibles).
- **Effect on the client's number:** The largest measured effect of any finding. Counting these 9 as standalones shrinks the franchise advantage from 3.6x to 2.1x (all years) and from 2.8x to 1.8x (from 2000). Franchise still wins in both windows.
- **What I did about it:** Kept the default rule (a collection is a franchise) and reported the alternative beside it; the franchise shortlist only considers collections with 3 or more listed films.
- **Residual risk:** Whether each studio bundles these films cannot be checked with the allowed data (question Q4).

### F-05: The standalone side of the comparison is small — Severity: High

- **What it is:** Only 16 of 112 films are outside a collection, and only 8 from 2000 onward.
- **How I detected it:** Stage 5 group sizes, outputs/quality_report.csv (check "films").
- **Scale:** All years: 96 franchise films (32 collections) vs 16 standalones. From 2000: 63 (24 collections) vs 8.
- **Effect on the client's number:** The standalone figure from 2000 rests on 8 films, so one film more or less moves it noticeably. The window Yaw trusts is the one with the least evidence.
- **What I did about it:** Group sizes are shown beside every figure; a verdict needs at least 5 independent units per side and must hold on the median, the mean and with each side's top film removed. No claim of statistical significance is made.
- **Residual risk:** The result from 2000 is directional, not proof.

### F-06: One film drives the standalone average — Severity: High

- **What it is:** Standalone revenue is uneven; collection revenue is not.
- **How I detected it:** Stage 5 skew table, outputs/quality_skew.csv.
- **Scale:** From 2000, standalone mean 354M vs median 283M; Inception alone is 29.6% of the group's revenue. Collection films: mean 793M vs median 787M, top film 5.9%.
- **Effect on the client's number:** The mean flatters standalones by one film's result. Measured: franchise still wins on the median, on the mean, and with Inception removed.
- **What I did about it:** The median is the headline figure (decision note), the mean is shown beside it, and the top-film-removed check is part of the verdict rule.
- **Residual risk:** With 8 films, even the median moves if one film is added or removed.

### F-03: Talent counts may reflect franchises, not people — Severity: High (talent ask)

- **What it is:** Many directors and lead actors appear on several films, often within one franchise, so "appears often" can mean "worked on a franchise" rather than "picks good films".
- **How I detected it:** Stage 4 counts of distinct films per person (outputs/join_report.csv); stage 7 talent tables count collections and standalone films per person.
- **Scale:** 13 of 66 directors and 19 of 48 lead actors have 3 or more films. After requiring films in 2 or more separate contexts, one director (Christopher Nolan: 1 franchise and 4 standalones) shows a signal outside a single series, and three of his films are already on the shortlist, so it is not independent evidence.
- **Effect on the client's number:** A person can look reliable only because their franchise did well, and negotiators would press a point the evidence does not support. This affects the talent ask only.
- **What I did about it:** Talent needs 3 or more films across 2 or more contexts, set before any result was viewed; collections and standalone films are shown for every person.
- **Residual risk:** On 112 films, the talent read is mostly "could not verify".

### F-09: More than a third of the films predate 2000, and revenue is not inflation-adjusted — Severity: Medium

- **What it is:** 41 of 112 films were released before 2000. TMDb revenue is stated in the money of its day (an assumption about the field; the API does not say).
- **How I detected it:** Stage 5, check "films_before_cutoff"; median release years per group in outputs/kpi_groups.csv.
- **Scale:** 41 of 112 films. All years, franchise films are slightly newer (median 2003 vs 1999.5); from 2000 the groups are almost the same age (2007 vs 2006).
- **Effect on the client's number:** Part of the all-years gap (3.6x) comes from older standalones looking smaller. From 2000, where the groups are the same age, the gap is still 2.8x.
- **What I did about it:** Every comparison is shown for all years and from 2000; no inflation adjustment is made because no index is in scope.
- **Residual risk:** If the two windows ever disagree, the 2000-onward result is the one to defend.

### F-10: A known franchise entry has no TMDb collection — Severity: Medium

- **What it is:** The Good, the Bad and the Ugly (1966) is the third film of a trilogy but has no collection in TMDb, so the rule "no collection = standalone" labels it standalone.
- **How I detected it:** Reading the 16 no-collection titles; the sequel title pattern found 0.
- **Scale:** 1 of 16 standalones.
- **Effect on the client's number:** Counting it as franchise shrinks the all-years gap from 3.6x to 2.7x; the 2000-onward result is unchanged (outputs/kpi_sensitivity.csv).
- **What I did about it:** The rule stays, with this film named as a known exception and tested both ways.
- **Residual risk:** At 500 titles the list cannot be read by eye; the sequel review list is the safeguard.

### F-11: Entry position describes the listed films, not the series — Severity: Medium

- **What it is:** Each franchise film is labelled first, middle or last by release date among the films of its collection that are on the list. The full size of a series is not in the allowed data.
- **How I detected it:** Stage 6 position counts, outputs/cleaning_report.csv.
- **Scale:** 41 middle films in 22 collections; 23 first, 23 last, 9 only listed, 16 standalone.
- **Effect on the client's number:** The "weak middle entries" test is exact where the whole series is listed (Harry Potter, 8 of 8) and approximate where it is not. Measured: middle films earn about the same as the other films of their series (0.995x); 12 of 22 collections have a middle below the average of first and last.
- **What I did about it:** Reported as "position among listed films"; the test uses only collections with 3 or more listed films.
- **Residual risk:** Labels change when next year's list adds earlier or later films.

### F-13: One film universe can appear as two collections — Severity: Medium (talent ask)

- **What it is:** TMDb lists Iron Man and The Avengers as separate collections, although they belong to one connected film series. The talent rule counts them as two independent contexts.
- **How I detected it:** Reading the qualifying talent in outputs/talent_leads.csv: Robert Downey Jr. reaches 2 contexts only through these two collections.
- **Scale:** 1 lead actor in the qualifying list; other shared universes may exist and cannot be detected from the allowed data.
- **Effect on the client's number:** Robert Downey Jr. looks like a signal across contexts when the evidence is one franchise. Negotiators should use him as a lever for the Avengers deal only.
- **What I did about it:** Reported; the memo treats his figure as franchise evidence only.
- **Residual risk:** The same effect can appear with other connected series next year; the talent table shows collections and standalone films so a reader can check.

### F-02: Five candidate ids do not exist on TMDb — Severity: Medium

- **What it is:** 5 ids that looked valid (8471293, 8471294, 9412887, 9412888, 7733901) returned "not found" from TMDb. They are far larger than every other id in the list (the rest are at most about 301,528).
- **How I detected it:** The fetch stage requested each id once; TMDb answered 404 for these five (outputs/fetch_manifest.csv). The live re-check confirmed all five are still not found.
- **Scale:** 5 of 117 fetchable ids (4.3%); 112 films go forward.
- **Effect on the client's number:** Recording them keeps the count reconciled (117 to 112). If any were meant to be real films, they are missing from the shortlist; the effect cannot be measured without knowing what they are.
- **What I did about it:** Recorded each as "not found" with the fetch time; credits were not requested for them; excluded from the analysis but counted in the reconciliation.
- **Residual risk:** They may be typing errors or ids from another system. Question Q2 asks Adjoa whether her tracker holds titles for them.

### F-01: The candidate list contains rows that are not usable TMDb ids — Severity: Low

- **What it is:** 10 of the 127 rows cannot be sent to the API as they are: a blank row (row 68), the text "N/A" (row 110), "-1" (row 29), an IMDb-style id "tt0468569" (row 94), and 6 ids listed twice (155, 278, 550, 603, 680, 1891). Profiling showed that tt0468569 is The Dark Knight, already on the list as 155 (see F-07), so only 3 rows are truly unusable and 7 are repeats.
- **How I detected it:** I read the file as text with blank rows kept, then classified every row with fixed rules. The result is in outputs/quarantine.csv.
- **Scale:** 10 of 127 rows (7.9%): 3 unusable, 7 repeats. 117 unique ids remain to fetch.
- **Effect on the client's number:** If invalid and repeated ids were allowed through, extraction would include failed requests and the same film could be counted more than once, distorting counts and averages. After classification, only unique fetchable ids go forward.
- **What I did about it:** Quarantined each row with its reason and row number. Repeated ids are fetched once, and nothing is deleted.
- **Residual risk:** What the 3 unusable rows were meant to be is unknown.

### F-04: Co-Director credits are not counted as directors — Severity: Low

- **What it is:** TMDb lists some people as "Co-Director", a separate job from "Director". The analysis counts only "Director".
- **How I detected it:** The Directing job counts (outputs/director_job_counts.csv), and a check that none of those people is also credited as Director on the same film.
- **Scale:** 7 Co-Director credits on 5 animated films (Ice Age, Ice Age: Dawn of the Dinosaurs, Monsters, Inc., Shrek the Third, Toy Story 2).
- **Effect on the client's number:** These 7 people are left out of the director ranking. Every film still has a Director credit, so no film is lost and the film counts do not change.
- **What I did about it:** Exact match on "Director"; adding "Co-Director" is a one-line change in the settings.
- **Residual risk:** Only someone near the minimum film count could change rank; Lee Unkrich, with 2 Co-Director credits, is the one known case.

### F-07: The Dark Knight was entered three times — Severity: Low

- **What it is:** tt0468569 is the IMDb id of The Dark Knight, already on the list as TMDb id 155 (rows 1 and 90).
- **How I detected it:** Stage 5 looked up each quarantined IMDb-format value in the fetched films' IMDb ids (check "quarantined_imdb_id_found_in_films").
- **Scale:** 1 row (row 94).
- **Effect on the client's number:** None; the film is analysed once. It shows that the three source lists overlap and use different id systems.
- **What I did about it:** Row 94 is a verified repeat; unusable rows fall from 4 to 3.
- **Residual risk:** None for this row.

### F-12: The cleaning rules for zeros and unreleased films change nothing in this list — Severity: Low

- **What it is:** No film has a zero or missing budget or revenue, none is unreleased, and none is dated after the fetch.
- **How I detected it:** Stage 6 cleaning report: 0 rows affected for each of these rules.
- **Scale:** 0 of 112 films.
- **Effect on the client's number:** None today.
- **What I did about it:** The rules stay as insurance for next year's list, labelled as such. The timing test planted zeros and unreleased films in synthetic lists, and the rules caught all of them (7 and 4 at 500 titles).
- **Residual risk:** None for this list.

### F-14: The analysis reproduces the source, and nothing has changed that moves the answer — Severity: Low

- **What it is:** A live re-check of 13 films chosen for risk (messiest parsing, extremes, films affected by a decision, the shortlist boundaries) plus the 5 not-found ids.
- **How I detected it:** Stage 9 spot-check, outputs/spotcheck.csv and spotcheck_summary.csv; live responses kept in outputs/spotcheck_live/.
- **Scale:** 130 of 130 fields match between our tables and what was fetched; 128 of 130 match the live source exactly, 2 ratings drifted within the 0.1 tolerance; all 5 not-found ids are still not found.
- **Effect on the client's number:** None. The verdict, the strongest franchise and all 8 shortlisted titles are unchanged; the strongest franchise leads the second by 1.77 times per film in both windows.
- **What I did about it:** Nothing needed; the analysis stays on the fetched snapshot, with its as-of date.
- **Residual risk:** Both sides come from the same source, so this does not show the source's revenue is correct; 13 risk-weighted films are not the whole list (up to about 1 in 5 could still differ elsewhere); retries during the first fetch were not recorded.

## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| The file uses Windows line endings | It differs from the Linux files around it | It does not change any value, and it is stored unchanged in git (.gitattributes) |
| 9 films have two or more directors | It could look like repeated rows from the join | They are real co-directing credits (the Wachowskis, the Russos). The 122 Director credits equal 112 films plus 10 extra: one extra on each of 8 films and two on Shrek 2 (three directors), so the totals reconcile. The films table keeps one row per film, with the names in `director_names` and the count in `n_directors` |
| No film has a missing or zero budget or revenue | Zeros were expected on TMDb | All 112 have both values; the zero rule stays to protect next year's list but changes nothing today |
| Some budgets are very small (The Good, the Bad and the Ugly: $1.2M) | Could be values entered in millions | They match the era of the films; the 10 lowest are all real productions |
| Extreme revenue/budget ratios (Star Wars 70x, Jaws 67x) | Look like data errors | They are known breakout hits, not entry mistakes |
| Two ratings changed within a day of fetching | Could suggest the fetched data is unreliable | Ratings move daily by design; both changes were within the tolerance set in advance, and ratings are not the measure the recommendation rests on |
| Pirates of the Caribbean and The Hobbit are 0.3% apart (962M vs 958M per film) | The third franchise pick could look arbitrary | The ranking rule was fixed before results were viewed; the memo names The Hobbit as the alternative, so the negotiator can switch if Pirates is priced high |

## Could not verify

- What the five "not found" ids (8471293, 8471294, 9412887, 9412888, 7733901) were meant to be; they may be typos or ids from another system.
- What the 3 unusable rows (blank, "N/A", "-1") were meant to be.
- Whether each franchise in the list is the complete bundle the studio sells, and whether a film alone from its collection is sold on its own (no collection data in scope).
- Licence prices: the analysis measures audience demand (box office), not what each title would cost StreamVault.
- Streaming demand: box office measures cinema audiences, which stand in for streaming viewing; no viewing data is in scope.
- Revenue in today's money (no inflation index in scope).
- Which five-film bundle the competitor licensed, so whether passing on it was right.
- Whether TMDb's revenue figures are correct: the live re-check compares TMDb with itself.
- Results describe these candidates, which are mostly well-known hits, not films in general.