"""Stage 3: turn cached JSON into tables of a stated grain."""


def build_tables(raw_dir):
    """Flatten cached responses into three tables.

    Takes:   folder of cached JSON files
    Returns: films  (one row per film)
             cast   (one row per film per cast member)
             crew   (one row per film per crew member)
    Asserts: films has one row per successful movie response
             film ids are unique in films
    """
    raise NotImplementedError("Stage 3 - built in Phase 3")