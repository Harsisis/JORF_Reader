import pandas as pd

class ExcelManager:
    @staticmethod
    def save_to_excel(data, file_path="output.xlsx", sheet_name="Data"):
        
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        print(f"Data saved in {file_path}")
