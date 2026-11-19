# Decision notes

Every judgement call the brief left open. Major decisions have their own record (house template); smaller ones are in the table below. Each states what was decided, the alternative, what it costs Kwame if wrong, and what the recommendation looks like under the alternative.

| ADR | Decision | Stage |
|---|---|---|
| [001](ADR-001-quarantine-and-accounting.md) | Quarantine unusable rows with a reason; let the API decide which ids exist | 1, 2 |
| [002](ADR-002-snapshot-and-what-is-committed.md) | Analyse a cached snapshot; commit neither the raw responses nor the outputs; commit a small reference result | 2, 10 |
| [003](ADR-003-franchise-definition.md) | A franchise is a film in a TMDb collection | 6 |
| [004](ADR-004-performance-measure.md) | Measure performance as box office per film, median first, with a fixed winner rule | 7 |
| [005](ADR-005-talent-rules.md) | Lead = top-billed; Director exact; talent needs 3+ films in 2+ contexts | 4, 7 |
| [006](ADR-006-insurance-rules.md) | Keep zero and unreleased rules as insurance, run before positions | 6 |
| [007](ADR-007-time-budget.md) | A cached rerun of 500 titles within 10 s | 8 |
| [008](ADR-008-spot-check.md) | Spot-check risky films by rule; the analysis stays on the snapshot | 9 |

## Smaller decisions

| Decision | Alternative rejected | Cost to Kwame if wrong | Recommendation under the alternative |
|---|---|---|---|
| Crew table is one row per person per job | One row per person | Counts and joins would be wrong | Cannot move it |
| Genres kept in one cell ("Action\|Drama") | One row per film per genre | None today; genre analysis needs one extra step | Cannot move it (no genre ask) |
| Co-directors in their own film x director table; films keep one row | Keep only the first director | 10 director credits would be lost | Cannot move it (talent only) |
| Lead tie-break: lowest billing, then lowest person id | Any order | None today (0 ties) | Cannot move it |
| 2000 window: release year 2000 or later, inclusive; a missing year is "unknown", counted (0 today) | Missing year counted as before 2000 | A film could silently leave the window | Cannot move it (0 missing) |
| Minimum 5 independent units per side (collections for franchises) | Count films, not collections | Harry Potter's 8 films would count as 8 pieces of evidence | Cannot move it (8 standalones and 24 collections from 2000 both pass) |
| Minimum group size set after group sizes were known | Set before | The threshold gives little protection at 8; the median, mean and top-removed checks carry the weight | Cannot move it |
| Franchise shortlist needs 3+ listed films | 2+ films | A median of 2 films is just their mean | Same three picks |
| Franchise ranking by median box office per film, ties by collection id | Total bundle box office | Totals reward bundles that simply have more films | Not computed; totals would favour Harry Potter (8 films) |
| Deal-note demand index against all other films | Against all films including itself | The franchise would inflate its own baseline | Same top franchise |
| Middle-entry test: count of collections whose middle is below first and last, plus each film against the other films of its series | Each film against a median that includes itself | Ratios pulled towards 1 | Same conclusion: middle entries are not weak |
| Rating tolerance 0.1 in the live check | Exact match | Daily rating drift reported as source changes | Cannot move it (ratings are not the measure) |
| Offline mode (skip the live check) | Always run the live check | None: the check stays available | Cannot move it |
| Standalone shortlist: the 5 highest box-office standalones, with rating and year shown | Rank by rating | Two picks are pre-2000; the memo names 2000-onward replacements | Ranking by rating would put Schindler's List and Spirited Away first; the shortlist changes, the franchise verdict does not |
| "The one number" for the deal note fixed in advance as the demand index (box office per film against all other films, 2000 onward) | Choose the most persuasive number after seeing results | A number picked afterwards invites hindsight | Same top franchise; 2.6x from 2000, 3.6x all years |

## What survives when Adjoa reruns this on 500 titles

**Runs unchanged:** every rule lives in the settings file and works on any list; the checks are generic (no ids or counts are typed in); the counts reconcile automatically; a cached rerun of 500 titles was measured at 3.4 seconds; the insurance rules were shown to catch zeros and unreleased films at 500 and 5,000 titles.

**Needs her input:** new unusable rows and new not-found ids (listed automatically, but someone must decide what they were meant to be); possible sequels without a collection (a review list, not a fix); the named-case list for franchise entries TMDb does not group; shared film universes in the talent table; whether studios bundle single-listed franchises.

**No longer valid after a rerun:** this year's figures, shortlist and deal note; the first/middle/last labels (they depend on which films are listed); the spot-check sample; the as-of date. A rerun produces its own versions of all of these.

**Revisit:** if the list passes about 1,700 titles (the measured point where a rerun reaches 10 seconds); if the two time periods ever disagree; if licence prices become available.