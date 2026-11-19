# Data findings — StreamVault

## Summary
(written at the end, once all findings are ranked)

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---|---|---|
| Rows in id_list.csv | 127 | | client input, read as text with blank rows kept |
| After load classification | 117 fetchable | −10 | 1 blank, 1 not a number, 1 non-positive, 1 IMDb-format id, 6 repeated ids |
| After fetching from TMDb | 112 found | −5 | 5 ids returned "not found" (404): 8471293, 9412887, 8471294, 9412888, 7733901 |

## Findings, ranked by risk
(ranked at the end; severities are provisional)

### F-01: The candidate list contains rows that are not usable TMDb ids — Severity: (to be ranked)

- **What it is:** 10 of the 127 rows cannot be sent to the API as they are: a blank row (row 68), the text "N/A" (row 110), "-1" (row 29), an IMDb-style id "tt0468569" (row 94), and 6 ids listed twice (155, 278, 550, 603, 680, 1891).
- **How I detected it:** I read the file as text with blank rows kept, then classified every row with fixed rules. The result is in outputs/quarantine.csv.
- **Scale:** 10 of 127 rows (7.9%). 117 unique ids remain to fetch.
- **Effect on the client's number:** If invalid and duplicate IDs were allowed through, extraction would include failed API requests and the same film could be counted multiple times. This would affect the franchise-versus-standalone analysis by distorting counts and averages. After classification and deduplication, only unique fetchable movie IDs proceed to extraction.
- **What I did about it:** I quarantined each row with its reason and row number. Repeated ids are fetched once, and nothing is deleted.
- **Residual risk:** A fetchable ID may still fail validation when checked against TMDb, because format validation does not guarantee the film exists. These cases are handled in Stage 2, where API responses provide evidence for any additional quarantining. The same film could also appear under two different IDs, for example a re-release; the repeat check only catches identical IDs, so this is tested later during profiling. Finally, the IMDb-style ID may point to a real film that is now left out of the analysis.

### F-02: Five candidate ids do not exist on TMDb — Severity: (to be ranked)

- **What it is:** 5 ids that looked valid (8471293, 8471294, 9412887, 9412888, 7733901) returned "not found" from TMDb. They are far larger than every other id in the list (the rest are at most about 301,528).
- **How I detected it:** the fetch stage requested each id once; TMDb answered 404 for these five. Recorded in outputs/fetch_manifest.csv.
- **Scale:** 5 of 117 fetchable ids (4.3%); 112 films go forward.
- **Effect on the client's number:** If these IDs had been silently dropped, Kwame would have no record that they were supplied but could not be matched to a TMDb film. This would make the final film count appear lower without explanation and could lead to questions about whether records were lost during processing. By recording them as "not found", the difference between the input count (117 fetchable IDs) and the analysis set (112 films) can be fully reconciled. If any of the five IDs were intended to represent valid films, their exclusion could also slightly reduce coverage of the client's catalogue.
- **What I did about it:** recorded each as "not found" with the fetch time; credits were not requested for them; they are excluded from the analysis but counted in the reconciliation.
- **Residual risk:** The underlying cause of these invalid IDs could not be verified. They may be typographical errors, IDs copied from a different film database, or incorrectly mapped records from one of the source files. If the IDs were intended to represent real films, those films will not appear in the final analysis until the correct identifiers are obtained. Further investigation with the data provider would be required to determine the original intended records.

### F-03: Talent counts may reflect franchises, not people
- **Detected by:** Stage 4 counts of distinct films per person. Of 66 directors,
  13 have 3 or more films; of 48 lead actors, 19 have 3 or more. The count treats
  every film alike, so a director with three entries in one franchise passes the
  same test as one with three unrelated films. The co-directed films point the same
  way: most are franchise entries (The Matrix ×3, Avengers ×2, Shrek ×2, Pirates of
  the Caribbean). Stage 4 does not yet measure how many of the 13 and 19 reach
  3 films through a single collection; stage 7 will.
- **Effect on the recommendation:** A person can look reliable only because their
  franchise did well. Kwame's negotiators would then credit that person with the
  franchise's results and press a point the evidence does not support. This affects
  the talent ask only; the franchise-versus-standalone comparison does not use these
  counts.
- **Handling:** Stage 7 counts each person's standalone films separately and reports
  distinct collections per person. The minimum film count is set in Phase 7 and
  recorded in an ADR before any talent results are viewed.
- **Residual risk:** With 112 films, few people may reach the minimum on standalone
  titles alone. If so, the talent answer is reported as "could not verify" and is not
  stated more firmly than the data allows.
- **Severity:** High (talent ask).

### F-04: Co-Director credits are not counted as directors
- **Detected by:** The Directing job counts, which show 7 Co-Director credits, and a
  check that none of those 7 people is also credited as Director on the same film.
- **Effect on the recommendation:** The 7 people, on 5 animated films (Ice Age,
  Ice Age: Dawn of the Dinosaurs, Monsters, Inc., Shrek the Third, Toy Story 2), are
  left out of the director ranking. Every film still has a Director credit, so no
  film is lost and the film counts do not change.
- **Handling:** The decision is an exact match on "Director". Adding "Co-Director" is
  a one-line change to `DIRECTOR_JOBS` in config, so the memo can state whether the
  answer changes under the alternative.
- **Residual risk:** Low. Only someone near the minimum film count could change rank;
  Lee Unkrich, with 2 Co-Director credits, is the one known case.
- **Severity:** Low.


## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| The file uses Windows line endings | It differs from the Linux files around it | It does not change any value, and it is stored unchanged in git (.gitattributes) |
| 9 films have two or more directors | It could look like repeated rows from the join | They are real co-directing credits (the Wachowskis, the Russos). The 122 Director credits equal 112 films plus 10 extra: one extra on each of 8 films and two on Shrek 2 (three directors), so the totals reconcile. The films table keeps one row per film, with the names in `director_names` and the count in `n_directors` |


## Could not verify
- tt0468569 is an IMDb-format ID. Resolving it would need an endpoint outside the brief (see ADR). It may be a real film, possibly one already on the list.
- What the five "not found" ids (8471293, 8471294, 9412887, 9412888, 7733901) were meant to be; they may be typos or ids from another system.