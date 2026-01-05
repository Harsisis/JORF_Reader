import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tarfile
import xml.etree.ElementTree as ET
import shutil
#from excel import ExcelManager

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
    def read_tar_gz_files(download_dir, destination_dir):
        
        for archive_name in os.listdir(download_dir):
            if archive_name.endswith(".tar.gz"):
                archive_path = os.path.join(download_dir, archive_name)

                with tarfile.open(archive_path, "r:gz") as tar:
                    print("---")
                    print(f"${archive_name[5:-7]}/jorf/global/conteneur/JORF/CONT/")
                    print("---")
                    for member in filter(lambda value: value.isfile() and "JORF/CONT/" in value.name and value.name.endswith(".xml"), tar.getmembers()):
                        print(member.name)
                        member.path = os.path.basename(member.name)
                        tar.extract(member, path=destination_dir)
                        xml_path = os.path.join(destination_dir, member.name)

                        try:
                            tree = ET.parse(xml_path)
                            root = tree.getroot()

                            date_publi = root.find(".//DATE_PUBLI")
                            if date_publi is not None:
                                date = date_publi.text
                                print(f"Published Date: {date}")
                            else:
                                date = "inconnu"
                                print(f"No date found within XML {member.path}")

                            # Renommer le fichier avec la date
                            new_filename = f"JORF_{date}.xml"
                            new_filepath = os.path.join(destination_dir, new_filename)

                            # Déplacer et renommer le fichier
                            shutil.move(xml_path, new_filepath)
                            print(f"File renammed to {new_filename}")

                        except ET.ParseError as e:
                            print(f"Parsing Error on {member.path}: {e}")


    @staticmethod
    def save_to_excel(xml_dir):
        data = []
        data.append({
                    "texte": ""
                })

        #ExcelManager.save_to_excel(data)
