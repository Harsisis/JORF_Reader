import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tarfile
import xml.etree.ElementTree as ET
import shutil
import unicodedata
from datetime import datetime, date


class JORF_MANAGER:

    _DECRET_TXT = "decret"
    _ARRETE_TXT = "arrete"
    _CIRCULAIRE_TXT = "circulaire"

    _XML_TAG_DATE_PUBLICATION = ".//DATE_PUBLI"
    _XML_TAG_TITLE = ".//TITRE"
    _XML_ATTR_TITRETXT = "titretxt"

    _XML_TAG_QUERY_LINKS = ".//TM[@niv='2'][TITRE_TM='Décrets, arrêtés, circulaires']//LIEN_TXT"



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
                        print(f"Extracting: {member.name}...")
                        member.path = os.path.basename(member.name)
                        tar.extract(member, path=destination_dir)
                        xml_path = os.path.join(destination_dir, member.name)

                        try:
                            tree = ET.parse(xml_path)
                            root = tree.getroot()

                            date_publi = root.find(JORF_MANAGER._XML_TAG_DATE_PUBLICATION)
                            if date_publi is not None:
                                date = date_publi.text
                                print(f"Published Date found: {date}")
                            else:
                                date = "NA"
                                print(f"No date found within XML {member.path}")

                            filepath_indexable = JORF_MANAGER._get_file_path(destination_dir, date)                           
                            
                            shutil.move(xml_path, filepath_indexable)
                            print(f"File renammed to {os.path.basename(filepath_indexable)}")

                        except ET.ParseError as e:
                            print(f"Parsing Error on {member.path}: {e}")



    """@Private
    Return file path built using destination_dir and date

    @param destination_dir
    @param date

    Returns:
        str: file path
    """
    @staticmethod
    def _get_file_path(destination_dir, date_value) -> str:
        new_filename = f"JORF_{date_value}.xml"
        return os.path.join(destination_dir, new_filename)



    """Read all XML present in dedicated folder and try to parse them to create dataset
    If provided, start_date and end_date will restrict the selection
    Document with no "Décret", "Arrêté" or "Circulaire" will be ignored and not added to the dataset 

    @param start_date
    @param end_date
    
    Returns:
        list: list of JORF summary object
    """
    @staticmethod
    def read_xml_folder(start_date = None, end_date = None):
        xml_folder = os.getenv('XML_FOLDER_NAME')
        data = []

        for xml_file in os.listdir(xml_folder):
            if xml_file.endswith(".xml"):
                print(f"Analysing file {xml_file}...")
                try:
                    tree = ET.parse(os.path.join(xml_folder, xml_file))
                    root = tree.getroot()

                    publication_date = JORF_MANAGER._xml_get_date_publication(root)
                    publication_date_formatted = date.fromisoformat(publication_date)
                    if (start_date is not None and publication_date_formatted >= start_date) and (end_date is not None and publication_date_formatted <= end_date):
                        lien_decret_txts = []
                        lien_arrete_txts = []
                        lien_circulaire_txts = []
                        lien_autre_txts = []

                        link_nodes = root.findall(JORF_MANAGER._XML_TAG_QUERY_LINKS)
                        if link_nodes is not None:
                            print(f"{len(link_nodes)} link(s) found")
                            for lien_txt in link_nodes:
                                normalized = JORF_MANAGER.normalize_text(lien_txt.get(JORF_MANAGER._XML_ATTR_TITRETXT))
                                if JORF_MANAGER._DECRET_TXT in normalized:
                                    lien_decret_txts.append(lien_txt.get(JORF_MANAGER._XML_ATTR_TITRETXT))
                                elif JORF_MANAGER._ARRETE_TXT in normalized:
                                    lien_arrete_txts.append(lien_txt.get(JORF_MANAGER._XML_ATTR_TITRETXT))
                                elif JORF_MANAGER._CIRCULAIRE_TXT in normalized:
                                    lien_circulaire_txts.append(lien_txt.get(JORF_MANAGER._XML_ATTR_TITRETXT))
                                else:
                                    lien_autre_txts.append(lien_txt.get(JORF_MANAGER._XML_ATTR_TITRETXT))

                        
                        print(f"{len(lien_decret_txts)} 'Décret(s)' found...")
                        print(f"{len(lien_arrete_txts)} 'Arrêté(s)' found...")
                        print(f"{len(lien_circulaire_txts)} 'Circulaire(s)' found...")
                        print(f"{len(lien_autre_txts)} remaining link(s) found...")

                        if len(lien_decret_txts) <= 0 and len(lien_arrete_txts) <= 0 and len(lien_circulaire_txts) <= 0:
                            print(f"{xml_file} does not contain any 'Décret(s)', 'Arrêté(s)' or 'Circulaire(s)' and will not be taken into account")
                            continue

                        data.append({
                                "titre": JORF_MANAGER._xml_get_title(root),
                                "date publication": publication_date,
                                "nb decrets": len(lien_decret_txts),
                                "decrets": lien_decret_txts,
                                "nb arretes": len(lien_arrete_txts),
                                "arretes": lien_arrete_txts,
                                "nb circulaires": len(lien_circulaire_txts),
                                "circulaires": lien_circulaire_txts,
                                "nb autres":  len(lien_autre_txts),
                                "autres":  lien_autre_txts
                        })
                except ET.ParseError as e:
                    print(f"Reading Error on {xml_file}: {e}")

                print(f"Analysis done for file {xml_file}\n")
        return data
    


    """@Private
    Normalize text

    @param text

    Returns:
        str: normalized text
    """
    @staticmethod
    def normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text.lower()



    """@Private
    Get element title from content

    @param xml_content

    Returns:
        str: JORF title element
    """
    @staticmethod
    def _xml_get_title(xml_content) -> str:
        node = xml_content.find(JORF_MANAGER._XML_TAG_TITLE)
        if node is not None:
            return node.text
        return "NA"



    """@Private
    Get element title from content

    @param xml_content

    Returns:
        str: JORF title element
    """
    @staticmethod
    def _xml_get_date_publication(xml_content) -> str:
        node = xml_content.find(JORF_MANAGER._XML_TAG_DATE_PUBLICATION)
        if node is not None:
            return node.text
        return "NA"
    
