import re
import pandas as pd
import os
import sqlite3

def preprocess_des_file(file_path : str, pattern : str = None, sep : str = "|",
                     names : list = ["Name", "Description", "Type", "Start",
                                     "Length"]) -> pd.DataFrame:
    """
    A minimal function to read and preprocess the *.des file, which includes 
    parsing information for the corresponding *.dat file.

    Args:
        file_path (str): The path to the *.des file.
        pattern (str): The regex file for parsing the file. Set to `None` by
        default. If `None` it will use "(?<=\S)\s{3,}(?=\S)" to parse the
        document.
        sep (str): A separator for pandas to use in serializing the `DataFrame`.
        names (list): A list of strings containing the names for the table.

    Returns:
        DataFrame: The data read as a Pandas DataFrame.
    """
    assert os.path.exists(file_path), f"Error: Path {file_path} does not exist."
    assert isinstance(sep, str) and len(sep) == 1, f"Error: The separator ({sep}) must be a single character."
    assert isinstance(pattern, str) or pattern is None, f"Error: The pattern ({pattern}) must be a string." 

    # Create an empty list to populate with the contents of each line from the 
    # *.des file. As the loop iterates, lines are processed to change the three
    # or more spaces into the appropriate separators, which Pandas will later 
    # use. Each line is appended to the temporary list.
    temp = []
    with open(file_path, "r") as f:
        lines = f.readlines()
    for line in lines:
        if pattern is None:
            pattern = "(?<=\S)\s{3,}(?=\S)"
        updated_text = re.sub(pattern, sep, line)
        temp.append(updated_text.strip())

    # Split lines within the temporary list by the separator, then convert the 
    # output to a Pandas DataFrame. Assign the names argument to the DataFrame 
    # column names. Then evaluate if the first line is identical to the names
    # list. If so, the first line is suppressed.
    out = [line.split(sep) for line in temp]
    out = pd.DataFrame(out)
    out.columns = names
    if names == list(out.iloc[0]):
        out = out.iloc[1:]

    return out

def get_date_cols(df: pd.DataFrame, var: str = "Name", type: str = "Type", 
                  value: str = None) -> dict:
    """
    A minimal function to generate a dictionary of date variable names and their 
    corresponding data types.

    Args:
        df (pd.DataFrame): A pandas DataFrame representing the *.des file for 
        each data set.
        var (str): A string denoting the variable containing the name.
        type (str): A string denoting the variable containing the type.
        value (str): A string denoting the coding for date variables.

    Returns:
        Dictionary: A Python dictionary where the keys are variable names and
        the values represent the `DATE` data type. 
    """
    assert isinstance(df, pd.DataFrame), "The df must by a Pandas DataFrame object"
    assert var in df.columns, f"var ({var}) must be a valid column header name for the DataFrame."
    assert type in df.columns, f"type ({type}) must be a valid column header name for the DataFrame."
    
    # Transform DataFrame to a dictionary where the key represents the variable
    # name and the value is the data type listed in the *.des file.
    out = {}
    for index, row in df.iterrows():
        out[row[var]] = row[type]

    # If None, set up `value` to the appropriate string filter for the 
    # dictionary comprehension.
    if value is None:
        value = "DATE"
    out = {k: v for k, v in out.items() if v == value}

    return out

def preprocess_dat_file(dat_path: str, des_path: str, fix_dates: bool = True,
                        subset: int = None
                        ) -> pd.DataFrame:
    """
    A routine to ingest and preprocess the data in a *.dat file. In order to do
    so, the *.dat file must be accompanied by a matching *.des file, which
    contains instructions on how to parse the text contents of the *.dat file. 

    Args:
        dat_path (str): The path to the *.dat file.
        des_path (str): The path to the *.des file.
        fix_dates (bool): A logical, defaults to `True`, which enables the
        function to transform date variables from strings to dates.
        subset (int): For testing purposes, when not None it indicates how many
        rows should be read. 
    
    Return:
        DataFrame: A tabular representation of the *.dat data as a Pandas 
        DataFrame.
    """
    assert os.path.exists(dat_path), f"Error: Path {dat_path} does not exist."
    assert os.path.exists(des_path), f"Error: Path {des_path} does not exist."

    # Preprocess the *.des file and then extract date variables for recoding.
    des = preprocess_des_file(des_path)
    dt = get_date_cols(des)

    out = []
    with open(dat_path, "r") as f:
        lines = f.readlines()

    if subset is not None:
        lines = lines[0:subset]

    for line in lines:
        temp = {}
        for index, row in des.iterrows():
            start = int(row["Start"]) - 1
            end = start + int(row["Length"])
            if row["Name"] in dt.keys() and fix_dates:
                temp[row["Name"]] = pd.to_datetime(line.strip()[start:end],
                                                   errors="coerce").date()
            else:
                temp[row["Name"]] = line.strip()[start:end]
        out.append(temp)
    
    # Reshape as a DataFrame.
    df = pd.DataFrame(out) 
    
    return df

def list_unique_files(dir_path: str, extensions: tuple = (".dat", ".des")) -> dict:
    """
    Returns a dictionary of grouped files in a directory with the specified 
    extensions.

    Args:
        dir_path (str): A directory path containing *.des and *.dat files.
        extensions (tuple): A tuple with the valid extensions.

    Returns:
        Dictionary: A nested dictionary of file names (keys) at the highest
        level and the corresponding data and description file paths.
    """
    assert os.path.exists(dir_path), f"Error: Path {dir_path} does not exist."
    assert isinstance(extensions, tuple), "The extensions argument must be a tuple."

    files = [file.split(".")[0] for file in os.listdir(dir_path) if file.endswith(tuple(extensions))]
    npath = lambda a,b,c: os.path.join(a, f"{b}{c}")
    out = {file:{"dat": npath(dir_path, file, ".dat"),
                 "des": npath(dir_path, file, ".des"),
                 "ids": file} for file in files}
    
    return out

def process_table(kvcombo: dict, **kwargs) -> dict:
    """
    A routine to process individual *.dat files in conjunction with its
    corresponding *.des file. This ensures that both files are processed AND
    returned as a couple.

    Args:
        kvcombo (dict): A dictionary with a "dat" key corresponding to the data 
        path for a *.dat file and a "des" key for the *.des file.
    
    Returns:
        Dictionary: A named dictionary where the key is the unique dataset name
        and nested within int are the data and description files after 
        preprocessing.
    """
    out = {}
    data = preprocess_dat_file(dat_path=kvcombo["dat"],
                               des_path=kvcombo["des"],
                                **kwargs)
    desc = preprocess_des_file(file_path=kvcombo["des"])
    out[kvcombo["ids"]] = {
        "data" : data,
        "desc" : desc
    }
    return out

def build_sqlite_db(db_name: str, dir_path: str, **kwargs):
    """
    A routine to generate an SQLite database from the *.dat and *des files
    within a specific directory.

    Args: 
        db_name (str): The name for the resulting database.
        dir_path (str): A directory path containing *.des and *.dat files.

    Returns: 
        None: It writes an SQLite file.
    """
    assert os.path.exists(dir_path), f"Error: Path {dir_path} does not exist."
    
    conn = sqlite3.connect(f"{db_name}.sqlite")
    
    files = list_unique_files(dir_path=dir_path)
    
    for file in files:
        print(f"Reading {file}...")
        temp = process_table(kvcombo=files[file], **kwargs)
        for key in temp.keys():
            for table in temp[key].keys():
                print(f"\t Writing:{file}_{table}\n")
                if table == "data":
                    temp[key][table].to_sql(name=f"{file}_{table}", con=conn,
                                            index=False,
                                            if_exists="replace")
                if table == "desc":
                    temp[key][table].to_sql(name=f"{file}_{table}", con=conn,
                                            index=False,
                                            if_exists="replace")
                # TODO fix the lack of PK.
                # if table == "data":
                #     sql_command = "ALTER TABLE {tablename} ADD PRIMARY KEY ({pk});".format(tablename=f"{file}_{table}", pk=temp[key][table].columns[0])
                #     print(sql_command)
                #     conn.execute(sql_command)
    conn.close()