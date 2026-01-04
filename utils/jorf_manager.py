import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from excel import ExcelManager

class JORF_MANAGER:
    """Download available JORF archive from given url

    Returns:
        Boolean: return the status of the download True if all available files are donwloaded, false otherwise
    """
    @staticmethod
    def download_tar_gz_files(download_dir, base_url="https://echanges.dila.gouv.fr/OPENDATA/JORF/?C=M;O=D"):
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('JORF_') and href.endswith('.tar.gz'):
                file_url = urljoin(base_url, href)
                filename = os.path.join(download_dir, href)

                if not os.path.exists(filename):
                    print(f"Downloading {href}...")
                    try:
                        with open(filename, 'wb') as f:
                            f.write(requests.get(file_url).content)
                    except requests.exceptions.RequestException as e:
                        print(f"Error while downloading {href}: {e}")
                        return False
                else:
                    print(f"{href} already exist, file will not be downloaded again.")
        return True

    """Open and read all JORF archives within provided folder and write result in excel file

    """
    @staticmethod
    def read_tar_gz_files(download_dir):
        data = []

        # TODO archive extraction

        data.append({
                    "texte": ""
                })

        ExcelManager.save_to_excel(data)
