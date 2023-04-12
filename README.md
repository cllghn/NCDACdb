# NCDACdb

A Python tool for downloading and creating a local database from files obtained through the North Carolina Department Of Adult Correction Offender Public Information [site](https://webapps.doc.state.nc.us/opi/downloads.do?method=view). The site provides a links to files of North Carolina Department of Adult Correction offender related data. The files contain all public information on all NC Department of Adult Correction offenders convicted since 1972. The data files are zipped and their approximate size is listed beside the file description.

The schema for the database is provided, [here](https://www.doc.state.nc.us/offenders/PublicTables.pdf).

## Usage Examples:

Install with pip:
```python
pip install -i https://test.pypi.org/simple/ NCDACdb==0.1.0
```

Download, and unzip all raw data:

```python
from NCDACdb.fetch import get_zipped_paths, unpack_zipped_paths

urls = get_zipped_paths()    
unpack_zipped_paths(url_list=urls, extract_path="rawdata")
```

Build a local SQLite database from the downloaded files:

```python
from NCDACdb.build import build_sqlite_db

build_sqlite_db(db_name="ncdacdb", dir_path="rawdata")
```

Downsize the database to only include records updated after January 1st, 2020:

```python
from NCDACdb.downsize import downsize_by_update

downsize_by_update(input_db='ncdacdb.sqlite',
                   output_db='sub_ncdacdb.sqlite', 
                   date_filter='2020-01-01')
```