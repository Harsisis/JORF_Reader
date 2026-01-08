from utils.jorf_manager import JORF_MANAGER
from utils.excel import ExcelManager
from dotenv import load_dotenv

load_dotenv()

JORF_MANAGER.download_tar_gz_files()
JORF_MANAGER.read_tar_gz_files()
data = JORF_MANAGER.read_xml_folder()

ExcelManager.save_to_excel(data)