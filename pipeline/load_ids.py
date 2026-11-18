"""Stage 1: load the client's id list and classify every row."""


def load_and_classify_ids(path):
    """Read id_list.csv exactly as given and label every row.

    Takes:   path to id_list.csv
    Returns: (fetchable, quarantine) DataFrames
             fetchable  = unique, valid ids to request from the API
             quarantine = every other row, with a reason
    Asserts: rows read == fetchable + quarantine (nothing lost)
             fetchable ids are unique
    """
    raise NotImplementedError("Stage 1 - built in Phase 1")