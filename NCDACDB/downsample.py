"""
Preamble

Due to the large size of the SQL database produced when building from 
the raw downloads, this set of functions downsize the data. The purpose is to
make is more manageable in memory for users with less RAM.

There are several approaches provided here:
    1. Downsize by update date: The Offender Profile table (OFNT3AA1) is filtered
    to only include the identifiers (CMDORNUM) for profiles updated after a
    certain date. Those unique identifiers are then used to filter other tables.
"""

import sqlite3
import os

"""Downsizing Approach 1: Downsize by update date"""
def extract_ids_by_update(db_path: str, date_filter: str,
                          table: str = 'OFNT3AA1_data', 
                          variable: str = 'DTOFUPDT') -> list:
    """
    Extract the IDs from the Offender Profile table based on a minimal date.

    Args:
        db_path (str): Input database name.
        date_filter (str): Date to filter by as a string in YYYY-MM-DD pattern.
        table (str): Defaults to the Offender Profile table (OFNT3AA1).
        variable (str): Date variable used to filter, default to 'DTOFUPDT'.

    Returns:
        List: A list of unique identifiers for profiles edited after a certain
        date.

    """
    assert os.path.exists(db_path), f"Error: Path {db_path} does not exist."

    # Connect to database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Filter the data
    c.execute(f'SELECT * FROM {table} WHERE {variable} >= \'{date_filter}\'')

    # Extract id column
    out = [row[0] for row in c.fetchall()]

    # Close the database connection
    conn.close()

    return out

def extract_datatables_and_ids(db_path: str, only_data: bool = True) -> dict:
    """
    Extract a dictionary of table names and variable names for DOC personal
    unique identifier.

    Args:
        db_path (str): Input database name.
        only_data (str): If True the function will only return tables with the
        postfix '_data'.
    
    Returns: A Python dictionary where keys represent table names and values the 
    variable names for the unique personal identifiers.
    """
    assert os.path.exists(db_path), f"Error: Path {db_path} does not exist."
    # Connect to database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get the names of all tables in the database
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_list = c.fetchall()

    # Loop through and get names of first column
    out = {}
    for table in table_list:
        if only_data:
            if table[0].endswith('_data'):
                c.execute("PRAGMA table_info({name})".format(name=table[0]))
                out[table[0]] = c.fetchone()[1]
        else: 
            c.execute("PRAGMA table_info({name})".format(name=table[0]))
            out[table[0]] = c.fetchone()[1]
    
    return out

def downsize_by_update(input_db: str, output_db: str, date_filter: str):
    """
    Downsizes a the NC DAC database by a temporal filter. The function clones 
    the larger database and filters by a date to retain only records newer than
    the filter parameter.

    Args:
        input_db (str): Input database name.
        output_db (str): Output database name.
        date_filter (str): Date to filter by as a string in YYYY-MM-DD pattern.
    Return:
        None: Stores a new *.sqlite database.
    """
    assert os.path.exists(input_db), f"Error: Path {input_db} does not exist."
    assert not os.path.exists(output_db), f"Error: Path {output_db} already exists."

    # Connect to current and new databases
    conn_orig = sqlite3.connect(input_db)
    c_orig = conn_orig.cursor()
    conn_new = sqlite3.connect(output_db)
    c_new = conn_new.cursor()

    # Get filter ids and table-variable pairings
    wanted_list = extract_ids_by_update(input_db, date_filter)
    wanted_ids = ','.join(f"\'{id}\'" for id in wanted_list)
    tvar_pairs = extract_datatables_and_ids(input_db, False)

    # Attach the original database to the new database
    c_new.execute(f"ATTACH \'{input_db}\' AS orig")
    
    # Cycle over tables
    for table in tvar_pairs.keys():
        varname = tvar_pairs[table]
        if table.endswith('_data'):
            # Create a new table in the new database with a filtered copy
            c_new.execute(f"CREATE TABLE {table} AS SELECT * FROM orig.{table} WHERE {varname} IN ({wanted_ids})")
        else:
            c_new.execute(f"CREATE TABLE {table} AS SELECT * FROM orig.{table}")
       
    # Detach the original database from the new database
    c_new.execute("DETACH orig")

    # Close the database connections
    conn_orig.close()
    conn_new.close()