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


## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| The file uses Windows line endings | It differs from the Linux files around it | It does not change any value, and it is stored unchanged in git (.gitattributes) |

## Could not verify
- tt0468569 is an IMDb-format ID. Resolving it would need an endpoint outside the brief (see ADR). It may be a real film, possibly one already on the list.
- What the five "not found" ids (8471293, 8471294, 9412887, 9412888, 7733901) were meant to be; they may be typos or ids from another system.