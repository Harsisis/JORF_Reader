from utils.jorf_manager import JORF_MANAGER
from utils.excel import ExcelManager
from dotenv import load_dotenv
from datetime import date

load_dotenv()

JORF_MANAGER.download_tar_gz_files()
JORF_MANAGER.read_tar_gz_files()
data = JORF_MANAGER.read_xml_folder(date(2024, 7, 16), date(2025, 9, 5))

ExcelManager.save_to_excel(data)