import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tarfile
import xml.etree.ElementTree as ET
import shutil


class JORF_MANAGER:
    """Download available JORF archive from given url

    Returns:
        Boolean: return the status of the download True if all available files are downloaded, False otherwise
    """
    @staticmethod
    def download_tar_gz_files():
        download_dir = os.getenv('ARCHIVE_FOLDER_NAME')
        target_url = os.getenv('TARGET_URL')

        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('JORF_') and href.endswith('.tar.gz'):
                file_url = urljoin(target_url, href)
                filename = os.path.join(download_dir, href)

                if not os.path.exists(filename):
                    print(f"Downloading {href}...")
                    try:
                        with open(filename, 'wb') as f:
                            f.write(requests.get(file_url).content)
                    except requests.exceptions.RequestException as e:
                        print(f"Error while downloading {href}: {e}")
                else:
                    print(f"{href} already exist, file will not be downloaded again.")



    """Open and read all JORF archives within provided folder to get all JORF XML files

        Returns:
            Boolean: return the status of the extraction True if all available files are extracted and renammed correctly, False otherwise
    """
    @staticmethod
    def read_tar_gz_files():
        download_dir = os.getenv('ARCHIVE_FOLDER_NAME')
        destination_dir = os.getenv('XML_FOLDER_NAME')

        for archive_name in os.listdir(download_dir):
            if archive_name.endswith(".tar.gz"):
                archive_path = os.path.join(download_dir, archive_name)

                with tarfile.open(archive_path, "r:gz") as tar:
                    for member in filter(lambda value: value.isfile() and "JORF/CONT/" in value.name and value.name.endswith(".xml"), tar.getmembers()):
                        print(f"Extracting: ${member.name}...")
                        member.path = os.path.basename(member.name)
                        tar.extract(member, path=destination_dir)
                        xml_path = os.path.join(destination_dir, member.name)

                        try:
                            tree = ET.parse(xml_path)
                            root = tree.getroot()

                            date_publi = root.find(".//DATE_PUBLI")
                            if date_publi is not None:
                                date = date_publi.text
                                print(f"Published Date found: {date}")
                            else:
                                date = "NA"
                                print(f"No date found within XML {member.path}")

                            new_filename = f"JORF_{date}.xml"
                            new_filepath = os.path.join(destination_dir, new_filename)

                            shutil.move(xml_path, new_filepath)
                            print(f"File renammed to {new_filename}")

                        except ET.ParseError as e:
                            print(f"Parsing Error on {member.path}: {e}")



    @staticmethod
    def read_xml_folder():
        xml_folder = os.getenv('XML_FOLDER_NAME')
        data = []

        for xml_file in os.listdir(xml_folder):
            if xml_file.endswith(".xml"):
                print(f"Analysing file ${xml_file}...")
                try:
                    tree = ET.parse(os.path.join(xml_folder, xml_file))
                    root = tree.getroot()

                    lien_txts = []
                    for titre_tm in root.iter("TITRE_TM"):
                        if titre_tm.text == "Décrets, arrêtés, circulaires":
                            parent = titre_tm.getparent() #TODO
                            if parent is not None:
                                for sibling in parent.iter():
                                    if sibling.tag == "TM" and sibling.get("niv") == "3":
                                        for tm in sibling.iter():
                                            if tm.tag == "LIEN_TXT":
                                                lien_txts.append(tm.get("titretxt"))
                    
                    print(f"${len(lien_txts)} link found...")

                    data.append({
                            "titre": JORF_MANAGER._xml_get_title(root),
                            "date_publication": JORF_MANAGER._xml_get_date_publication(root),
                            "liens": lien_txts
                    })
                except ET.ParseError as e:
                    print(f"Reading Error on {xml_file}: {e}")
        return data
    
    @staticmethod
    def _xml_get_title(xml_content) -> str:
        return xml_content.find(".//TITRE")

    @staticmethod
    def _xml_get_date_publication(xml_content) -> str:
        return xml_content.find(".//DATE_PUBLI")
    
