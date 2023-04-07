import requests
import zipfile
from bs4 import BeautifulSoup
import os

def get_zipped_paths(url: str = None) -> list:
    """
    Fetch the URLs to zipped files in the North Carolina Department of Adult
    Correction Offender Public Information downloads site.

    Args:
        url (str): The URL you to the downloads site. Default is none, if so,
        the function uses 'https://webapps.doc.state.nc.us/opi/downloads.do?method=view'.
    
    Returns:
        list: A list of URLs ending in *.zip.
    """
    assert url is None or isinstance(url, str), "url must be a string or None."
    if url is None:
        url = 'https://webapps.doc.state.nc.us/opi/downloads.do?method=view'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    zip_urls = [link['href'] for link in soup.find_all('a', href = True) if link['href'].endswith('zip')]
    return zip_urls

def unzip_file(zip_path: str, extract_path: str = None):
    """
    Unzip files.

    Args:
        zip_path (str): A path to a zipped file which is unzipped.
        extract_path (str): A path to store unzipped files, in `None` it will 
        use the parent directory for the zipped file. Default is `None`.
    """
    if extract_path is None:
        extract_path = os.path.dirname(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def download_file(url: str, extract_path: str, local_name: str = None, unzip: bool = True, cleanup: bool = True):
    """
    Download files from a URL

    Args:
        url (str): The URL to a zipped file.
        extract_path (str): The destination path.
        local_name (str): Local name for the download. In `None`, the last particle
        of the URL is used.
        unzip (bool): If `True`, the function unzips the file. Defaults to `True`.
    """
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise ValueError(f'Failed to make request to {url}') from e
    
    if local_name is None: 
        local_name = url.split('/')[-1]
    file_path = os.path.join(extract_path, local_name)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    
    if unzip:
        unzip_file(zip_path=file_path)

    if cleanup:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
        except PermissionError:
            print(f"Permission denied while trying to delete '{file_path}'.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")

def unpack_zipped_paths(url_list: list, extract_path: str, **kwargs):
    """
    """
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    for url in url_list:
        download_file(url=url, extract_path=extract_path, **kwargs)