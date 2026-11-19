"""Improvement beyond the brief: what changed since the last saved result, and why?

Usage:  python -m pipeline.compare_runs            compare outputs/ with the latest snapshot
        python -m pipeline.compare_runs --save     save outputs/ as a new dated snapshot
        python -m pipeline.compare_runs --demo     show the report on a made-up 'previous quarter'
A change can come from three places: the candidate list, the TMDb data, or our own settings and
code. Each snapshot stores a fingerprint of each, so the report can say which one moved.
Writes outputs/change_report.md.
"""
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import config

TABLES = ["kpi_comparison", "shortlist_franchise", "shortlist_standalone", "deal_note"]
REVENUE_CHANGE_MIN = 0.01        # a box-office revision counts only if it is 1% or more


def _list_fingerprint():
    """Hash of the sorted, de-duplicated ids: re-sorting the file does not count as a change."""
    ids = pd.read_csv(config.ID_LIST_PATH, dtype=str, keep_default_na=False, skip_blank_lines=False)[config.ID_COLUMN]
    return hashlib.md5("\n".join(sorted(set(ids.str.strip()))).encode()).hexdigest()[:12]


def _settings_fingerprint():
    return hashlib.md5((Path(config.PROJECT_ROOT) / "config.py").read_bytes()).hexdigest()[:12]


def _code_fingerprint():
    """Hash of the pipeline's code files: changes only when the analysis code changes, not the documents."""
    root = Path(config.PROJECT_ROOT)
    files = sorted((root / "pipeline").glob("*.py")) + [root / "run_pipeline.py"]
    digest = hashlib.md5()
    for f in files:
        if f.exists() and f.name != "compare_runs.py":
            digest.update(f.read_bytes())
    return digest.hexdigest()[:12]


def current_result(out_dir=None):
    """The decision-level result of the run in outputs/, with fingerprints of where it came from."""
    out = Path(out_dir or config.OUTPUT_DIR)
    stamps = pd.read_csv(out / "fetch_manifest.csv")["fetched_at"]
    fetched = (pd.to_datetime(stamps, unit="s", errors="coerce", utc=True) if pd.api.types.is_numeric_dtype(stamps)
               else pd.to_datetime(stamps, errors="coerce", utc=True))
    films = pd.read_csv(out / "films_clean.csv")[["movie_id", "title", "revenue", "is_franchise", "collection_name"]]
    summary = {"id_list_fingerprint": _list_fingerprint(),
               "rows_in_list": len(pd.read_csv(out / "ids_classified.csv")),
               "films_analysed": len(films),
               "fetched_from": f"{fetched.min():%Y-%m-%d}", "fetched_to": f"{fetched.max():%Y-%m-%d}",
               "settings_fingerprint": _settings_fingerprint(), "code_fingerprint": _code_fingerprint()}
    return summary, films, {t: pd.read_csv(out / f"{t}.csv") for t in TABLES}


def save_snapshot(target_root=None, result=None):
    summary, films, tables = result or current_result()
    root = Path(target_root or config.SNAPSHOT_DIR)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder, n = root / stamp, 1
    while folder.exists():                                   # never overwrite an earlier snapshot
        n += 1
        folder = root / f"{stamp}_{n}"
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(json.dumps(summary, indent=2))
    films.to_csv(folder / "films.csv", index=False)
    for name, table in tables.items():
        table.to_csv(folder / f"{name}.csv", index=False)
    return folder


def load_snapshot(folder):
    folder = Path(folder)
    return (json.loads((folder / "summary.json").read_text()), pd.read_csv(folder / "films.csv"),
            {t: pd.read_csv(folder / f"{t}.csv") for t in TABLES})


def _margin(tables):
    """Strongest franchise's box office per film over the second's (from the shortlist)."""
    m = tables["shortlist_franchise"]["median_revenue"].astype("float64")
    return m.iloc[0] / m.iloc[1] if len(m) > 1 else float("nan")


def compare(previous, current, label_prev, label_cur):
    (ps, pf, pt), (cs, cf, ct) = previous, current
    lines = [f"# What changed: {label_prev} -> {label_cur}", ""]

    lines += ["## Where a change could come from", "", "| | Previous | Current | Changed? |", "|---|---|---|---|"]
    rows = [("id_list_fingerprint", "Candidate list (fingerprint of the ids)"), ("rows_in_list", "Rows in the list"),
            ("films_analysed", "Films analysed"), ("fetched_from", "TMDb data fetched from"),
            ("fetched_to", "TMDb data fetched to"), ("settings_fingerprint", "Settings (fingerprint)"),
            ("code_fingerprint", "Analysis code (fingerprint)")]
    for key, name in rows:
        a, b = ps.get(key, "n/a"), cs.get(key, "n/a")
        lines.append(f"| {name} | {a} | {b} | {'**yes**' if a != b else 'no'} |")
    sources = []
    if ps.get("id_list_fingerprint") != cs.get("id_list_fingerprint"):
        sources.append("the candidate list changed")
    if (ps.get("fetched_from"), ps.get("fetched_to")) != (cs.get("fetched_from"), cs.get("fetched_to")):
        sources.append("the TMDb data was fetched at a different time")
    if (ps.get("settings_fingerprint"), ps.get("code_fingerprint")) != (cs.get("settings_fingerprint"), cs.get("code_fingerprint")):
        sources.append("the settings or the code changed")
    lines += ["", "Reading: " + ("; ".join(sources) if sources else "same list, same data, same settings and code") + ".",
              "Box office can only be revised if the cached TMDb data was refreshed (README, rerunning next quarter).", ""]

    lines += ["## The decision", "",
              "| Period | Verdict (previous -> current) | Franchise lead | Strongest franchise's demand index |",
              "|---|---|---|---|"]
    pv, cv = pt["kpi_comparison"].set_index("window"), ct["kpi_comparison"].set_index("window")
    pdn, cdn = pt["deal_note"].set_index("window"), ct["deal_note"].set_index("window")
    flips = []
    for w in cv.index:
        a = pv.loc[w, "verdict"] if w in pv.index else "n/a"
        b = cv.loc[w, "verdict"]
        if a != b:
            flips.append(w)
        verdict = f"{a} -> **{b}**" if a != b else b
        lead = f"{pv.loc[w, 'gap_ratio_medians']:.1f}x -> {cv.loc[w, 'gap_ratio_medians']:.1f}x" if w in pv.index else "n/a"
        index = (f"{pdn.loc[w, 'demand_index']:.1f}x -> {cdn.loc[w, 'demand_index']:.1f}x"
                 if w in pdn.index and w in cdn.index else "n/a")
        lines.append(f"| {w} | {verdict} | {lead} | {index} |")
    lines += ["", f"**{'WARNING: the verdict changed in ' + ', '.join(flips) if flips else 'The verdict did not change.'}**", ""]

    pd_top, cd_top = set(pt["deal_note"]["collection_name"]), set(ct["deal_note"]["collection_name"])
    pfr, pst = set(pt["shortlist_franchise"]["collection_name"]), set(pt["shortlist_standalone"]["title"])
    cfr, cst = set(ct["shortlist_franchise"]["collection_name"]), set(ct["shortlist_standalone"]["title"])
    lines += ["## The shortlist and the deal note", "",
              f"- Strongest franchise: {', '.join(sorted(cd_top))}" + ("" if pd_top == cd_top else f" (was {', '.join(sorted(pd_top))})"),
              f"- Lead of the strongest franchise over the second: {_margin(pt):.2f}x -> {_margin(ct):.2f}x",
              f"- Franchise picks in: {', '.join(sorted(cfr - pfr)) or 'none'}; out: {', '.join(sorted(pfr - cfr)) or 'none'}",
              f"- Standalone picks in: {', '.join(sorted(cst - pst)) or 'none'}; out: {', '.join(sorted(pst - cst)) or 'none'}", ""]

    merged = pf.merge(cf, on="movie_id", how="outer", suffixes=("_prev", "_cur"), indicator=True)
    added, removed = merged[merged["_merge"].eq("right_only")], merged[merged["_merge"].eq("left_only")]
    both = merged[merged["_merge"].eq("both")]
    share = (both["revenue_cur"] - both["revenue_prev"]).abs() / both["revenue_prev"].abs()
    moved = both[share.ge(REVENUE_CHANGE_MIN)].assign(change=lambda d: d["revenue_cur"] - d["revenue_prev"]) \
        .sort_values("change", key=abs, ascending=False)
    relabelled = both[both["is_franchise_prev"].ne(both["is_franchise_cur"])]
    names = lambda s: ", ".join(s.head(10)) + ("..." if len(s) > 10 else "")
    lines += ["## Films", "",
              f"- Added: {len(added)}" + (f" ({names(added['title_cur'])})" if len(added) else ""),
              f"- Removed: {len(removed)}" + (f" ({names(removed['title_prev'])})" if len(removed) else ""),
              f"- Franchise label changed: {len(relabelled)}" + (f" ({names(relabelled['title_cur'])})" if len(relabelled) else ""),
              f"- Box office revised by {REVENUE_CHANGE_MIN:.0%} or more: {len(moved)}"]
    for r in moved.head(10).itertuples():
        lines.append(f"  - {r.title_cur}: {r.revenue_prev / 1e6:,.0f}M -> {r.revenue_cur / 1e6:,.0f}M")
    nothing = not sources and not flips and not len(added) and not len(removed) and not len(moved) and not len(relabelled)
    if nothing:
        lines += ["", "**No change at all: this run matches the saved result.**"]
    return "\n".join(lines) + "\n", bool(flips)


def _latest_snapshot():
    folders = sorted(p for p in Path(config.SNAPSHOT_DIR).glob("*") if (p / "summary.json").exists())
    if not folders:
        sys.exit(f"No snapshot in {config.SNAPSHOT_DIR}. Run with --save first.")
    return folders[-1]


def demo():
    """A made-up 'previous quarter' built from this run, with one change of each kind:
    a shorter list (3 titles not yet added), an earlier fetch with one revised figure, a different
    top standalone, and no clear winner from 2000."""
    summary, films, tables = current_result()
    pf = films.sort_values("revenue", ascending=False).reset_index(drop=True)
    revised = pf.loc[0, "title"]
    pf.loc[0, "revenue"] = int(pf.loc[0, "revenue"] * 0.9)
    new_titles = pf.loc[len(pf) - 3:, "title"].tolist()
    pf = pf.iloc[:-3]
    pt = {k: v.copy() for k, v in tables.items()}
    st = pt["shortlist_standalone"]
    swapped_out = st["title"].iloc[0]
    st.loc[st.index[0], "title"] = "The Departed"
    pt["kpi_comparison"].loc[pt["kpi_comparison"]["window"].eq("from_2000"), ["verdict", "gap_ratio_medians"]] = ["no clear winner", 1.2]
    ps = {**summary, "id_list_fingerprint": "previous-list", "rows_in_list": summary["rows_in_list"] - 3,
          "films_analysed": len(pf), "fetched_from": "2026-08-15", "fetched_to": "2026-08-15"}
    report, _ = compare((ps, pf, pt), (summary, films, tables), "made-up previous quarter", "this run")
    note = (f"(Demo: the previous quarter is made up from this run. It had 3 fewer titles ({', '.join(new_titles)}), "
            f"an earlier fetch in which {revised} was 10% lower, The Departed in place of {swapped_out}, "
            "and no clear winner from 2000.)\n\n")
    return note + report


def main():
    if "--save" in sys.argv:
        print(f"Saved snapshot: {save_snapshot()}")
        return
    if "--demo" in sys.argv:
        report = demo()
    else:
        folder = _latest_snapshot()
        report, _ = compare(load_snapshot(folder), current_result(), f"saved result {folder.name}", "this run")
    (Path(config.OUTPUT_DIR) / "change_report.md").write_text(report)
    print(report)
    print("-> outputs/change_report.md")


if __name__ == "__main__":
    main()