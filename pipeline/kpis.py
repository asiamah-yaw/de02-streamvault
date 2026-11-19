"""Stage 7 - the numbers Kwame asked for, for both windows. No loops over films.

Takes:   films_clean (stage 6), film_directors and film_leads (stage 4)
Returns: dict of tables, each written to outputs/<name>.csv by run_pipeline.py
Decided before any result was viewed (ADRs): revenue per film is the measure, median is the
headline, a winner needs enough independent units AND must win on median, on mean and with each
group's top film removed; otherwise "no clear winner".
"""
import numpy as np
import pandas as pd

import config

NO_WINNER = "no clear winner"


def _windows(films):
    return {"all_years": pd.Series(True, index=films.index),
            f"from_{config.WINDOW_CUTOFF_YEAR}": films["from_2000"].fillna(False).astype(bool)}


def _units(group):
    """Independent units: one per collection; a franchise film with no collection counts alone."""
    return group["collection_id"].nunique() + int(group["collection_id"].isna().sum())


def _side(f_value, s_value):
    return "franchise" if f_value > s_value else "standalone"


def _drop_top(rev):
    return rev.drop(rev.idxmax()) if len(rev) > 1 else rev


def _compare(films, is_franchise):
    """Group rows and the winner verdict for each window, for one franchise labelling."""
    usable = films[films["has_revenue"]].assign(is_franchise=is_franchise[films["has_revenue"]])
    groups, verdicts = [], []
    for window, mask in _windows(usable).items():
        w = usable[mask]
        f, s = w[w["is_franchise"]], w[~w["is_franchise"]]
        fr, sr = f["revenue"].astype("float64"), s["revenue"].astype("float64")
        for name, g, rev in [("franchise", f, fr), ("standalone", s, sr)]:
            groups.append({"window": window, "group": name, "films": len(g), "units": _units(g),
                           "median_revenue": rev.median(), "mean_revenue": rev.mean(),
                           "median_release_year": g["release_year"].median()})
        coll_medians = f.groupby("collection_id")["revenue"].median().astype("float64")
        checks = {"median": _side(fr.median(), sr.median()),
                  "mean": _side(fr.mean(), sr.mean()),
                  "top_film_removed": _side(_drop_top(fr).median(), _drop_top(sr).median())}
        enough = min(_units(f), _units(s)) >= config.MIN_GROUP_SIZE
        same = len(set(checks.values())) == 1
        verdicts.append({"window": window, "gap_ratio_medians": fr.median() / sr.median(),
                         **{f"wins_on_{k}": v for k, v in checks.items()},
                         "per_collection_side": _side(coll_medians.median(), sr.median()),
                         "enough_units": enough,
                         "verdict": checks["median"] if (enough and same) else NO_WINNER})
    return pd.DataFrame(groups), pd.DataFrame(verdicts)


def _loo_ratio(rev):
    """Each film's revenue / median of the OTHER listed films of its collection (vectorised)."""
    v = rev.to_numpy(dtype="float64")
    others = np.ma.masked_array(np.tile(v, (len(v), 1)), mask=np.eye(len(v), dtype=bool))
    return pd.Series(v / np.ma.median(others, axis=1).filled(np.nan), index=rev.index)


def _middle_entries(films):
    m = films[films["is_franchise"] & films["has_revenue"] & films["films_in_collection_list"].ge(3)].copy()
    m["loo_ratio"] = m.groupby("collection_id")["revenue"].transform(_loo_ratio)
    by_pos = m.pivot_table(index="collection_id", columns="entry_position", values="revenue", aggfunc="median")
    by_pos = by_pos.reindex(columns=["first", "middle", "last"])      # safe if a position is absent
    middle_below = by_pos["middle"] < by_pos[["first", "last"]].mean(axis=1)
    summary = (m.groupby("entry_position")["loo_ratio"].agg(films="size", median_ratio_to_others="median")
                 .reset_index())
    summary["collections_with_middle"] = len(by_pos)
    summary["collections_middle_below_first_last_avg"] = int(middle_below.sum())
    return summary


def _franchise_table(films, mask):
    f = films[mask & films["is_franchise"] & films["has_revenue"] & films["collection_id"].notna()]
    t = (f.groupby(["collection_id", "collection_name"])
           .agg(listed_films=("movie_id", "size"), median_revenue=("revenue", "median"),
                weakest_revenue=("revenue", "min"), median_rating=("vote_average", "median"),
                first_year=("release_year", "min"), last_year=("release_year", "max"))
           .reset_index())
    weakest = f.loc[f.groupby("collection_id")["revenue"].idxmin(), ["collection_id", "title"]]
    t = t.merge(weakest.rename(columns={"title": "weakest_film"}), on="collection_id", validate="one_to_one")
    t["weakest_share_of_median"] = t["weakest_revenue"] / t["median_revenue"]
    t = t[t["listed_films"].ge(config.MIN_SHORTLIST_FILMS)]
    return t.sort_values(["median_revenue", "collection_id"], ascending=[False, True]).reset_index(drop=True)


def _shortlists(films):
    fr = _franchise_table(films, pd.Series(True, index=films.index)).head(config.SHORTLIST_FRANCHISES)
    fr["reason"] = (fr["median_revenue"].div(1e6).round().astype(int).astype(str) + "M median revenue per film across "
                    + fr["listed_films"].astype(str) + " listed films; weakest listed film " + fr["weakest_film"]
                    + " at " + fr["weakest_share_of_median"].mul(100).round().astype(int).astype(str) + "% of that")
    s = films[~films["is_franchise"] & films["has_revenue"]].sort_values(["revenue", "movie_id"], ascending=[False, True])
    st = s.head(config.SHORTLIST_STANDALONES)[["movie_id", "title", "release_year", "from_2000", "revenue", "vote_average"]].copy()
    st["reason"] = (st["revenue"].div(1e6).round().astype(int).astype(str) + "M revenue, rated "
                    + st["vote_average"].round(1).astype(str) + ", released " + st["release_year"].astype(str)
                    + np.where(st["from_2000"].fillna(False), "", " (before 2000)"))
    return fr, st


def _talent(films, people, role):
    joined = people.merge(films[["movie_id", "revenue", "has_revenue", "collection_id", "is_franchise", "from_2000"]],
                          on="movie_id", how="left", validate="many_to_one", indicator=True)
    dropped = int(joined["_merge"].eq("left_only").sum())        # film excluded in stage 6
    joined = joined[joined["_merge"].eq("both") & joined["has_revenue"]].drop(columns="_merge")
    rows = []
    for window, mask in _windows(joined).items():
        w = joined[mask].assign(revenue=lambda d: d["revenue"].astype("float64"))
        wf = films[_windows(films)[window] & films["has_revenue"]]
        baseline = wf["revenue"].astype("float64").median()
        w = w.assign(above=w["revenue"].gt(baseline), standalone=w["collection_id"].isna())
        t = (w.groupby(["person_id", "name"])
               .agg(films=("movie_id", "nunique"), collections=("collection_id", "nunique"),
                    standalone_films=("standalone", "sum"), median_revenue=("revenue", "median"),
                    share_above_baseline=("above", "mean"))
               .reset_index())
        t["contexts"] = t["collections"] + t["standalone_films"]
        t["relative_to_baseline"] = t["median_revenue"] / baseline
        t["qualifies"] = t["films"].ge(config.MIN_TALENT_FILMS) & t["contexts"].ge(config.MIN_TALENT_CONTEXTS)
        t.insert(0, "window", window)
        t.insert(1, "role", role)
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    out = out.sort_values(["window", "qualifies", "relative_to_baseline", "person_id"],
                          ascending=[True, False, False, True]).reset_index(drop=True)
    return out, dropped


def _deal_note(films):
    rows = []
    for window, mask in _windows(films).items():
        t = _franchise_table(films, mask)
        if t.empty:
            rows.append({"window": window, "collection_name": None})
            continue
        top = t.iloc[0]
        others = films[mask & films["has_revenue"] & films["collection_id"].ne(top["collection_id"]).fillna(True)]
        rows.append({"window": window, "collection_id": int(top["collection_id"]),
                     "collection_name": top["collection_name"], "listed_films": int(top["listed_films"]),
                     "median_revenue": top["median_revenue"],
                     "median_revenue_all_other_films": others["revenue"].astype("float64").median(),
                     "demand_index": top["median_revenue"] / others["revenue"].astype("float64").median(),
                     "weakest_film": top["weakest_film"], "weakest_share_of_median": top["weakest_share_of_median"]})
    note = pd.DataFrame(rows)
    note["same_top_in_both_windows"] = note["collection_name"].nunique() == 1
    return note


def both_windows(films, film_directors, film_leads):
    films = films.copy()
    groups, verdict = _compare(films, films["is_franchise"])

    scenarios = {
        "default_collection_is_franchise": films["is_franchise"],
        "franchise_needs_2plus_listed": films["is_franchise"] & films["films_in_collection_list"].ge(2),
        "named_case_as_franchise": films["is_franchise"] | films["movie_id"].isin(list(config.SENSITIVITY_FRANCHISE_CASES)),
    }
    sens = []
    for name, labels in scenarios.items():
        moved = films.loc[labels.ne(films["is_franchise"]), "title"].tolist()
        _, v = _compare(films, labels)
        sens.append(v.assign(scenario=name, films_moved=len(moved), moved_titles="; ".join(moved)))
    sensitivity = pd.concat(sens, ignore_index=True)

    franchise_short, standalone_short = _shortlists(films)
    directors, dropped_d = _talent(films, film_directors, "director")
    leads, dropped_l = _talent(films, film_leads, "lead")
    note = _deal_note(films)

    verdict["windows_disagree"] = verdict["verdict"].nunique() > 1
    if verdict["windows_disagree"].any():
        print("  WARNING: THE RECOMMENDATION CHANGES BETWEEN WINDOWS:",
              dict(zip(verdict["window"], verdict["verdict"])))
    if not note["same_top_in_both_windows"].all():
        print("  WARNING: THE STRONGEST FRANCHISE DIFFERS BETWEEN WINDOWS:",
              dict(zip(note["window"], note["collection_name"])))

    return {"kpi_groups": groups, "kpi_comparison": verdict, "kpi_sensitivity": sensitivity,
            "middle_entries": _middle_entries(films), "shortlist_franchise": franchise_short,
            "shortlist_standalone": standalone_short, "talent_directors": directors,
            "talent_leads": leads, "deal_note": note,
            "talent_join_report": pd.DataFrame({"role": ["director", "lead"],
                                                "rows_dropped_film_excluded": [dropped_d, dropped_l]})}