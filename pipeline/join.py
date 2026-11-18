"""Stage 4: join tables and prove the join lost and duplicated nothing."""


def join_talent(films, cast, crew):
    """Attach lead actor and director information to films.

    Takes:   films, cast, crew tables from Stage 3
    Returns: film-level table with talent columns, plus match counts
    Asserts: row count before == row count after (no fan-out)
             every join uses validate= and indicator=True
    """
    raise NotImplementedError("Stage 4 - built in Phase 4")