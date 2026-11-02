"""
ExcelPorter
2025-03-27

Andrew Kotyck

Advantage Group International
"""


from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
import json

class ExcelPorter:
    """
    Updated ExcelPorter using classes for better organization
    Converts excel file into easily manipulatable data types for easier comparisons

    """
    ############################# EXCEL to RAW LIST #############################
    # ---------------------------- MAIN FUNCTIONS ---------------------------- #

    def loadExcelData_ll(filepath: str, sheetindex: int = 0, keepblankrows=False,
                           rowindexes: list = [0, 1], colindexes: list = [], 
                           rowIndexExclude = True, colIndexExclude = True) -> list[list[str]]:
        """
        load excel data into list of lists for easier manipulation\n Follows format: 
        [
        row[cell, cell, cell], 
        row[cell, cell, cell], 
        row[cell, cell, cell]
        ]
        """
        wb = load_workbook(filepath)
        #sheet = wb.active # <- this one or \/ this one
        #sheet = wb.get_sheet_by_name(wb.sheetnames[sheetindex]) # APPARENTLY DEPRECATED
        sheet = wb[wb.sheetnames[sheetindex]]
        outlist = []
        rowsize = len(sheet["1"])
        colsize = len(sheet["A"])
        
        def isrowempty(cellvalues: list) -> bool:
            emptystring = 'None'
            return all(cellval == emptystring for cellval in cellvalues)

        def symmetric_difference(list1: list, list2: list) -> list:
            set1: set[any] = set(list1)
            set2: set[any] = set(list2)
            symmetric_difference_set: set[any] = set1 ^ set2
            #print(set1, set2, symmetric_difference_set)
            return list(symmetric_difference_set)

        skiprows = rowindexes if rowIndexExclude else symmetric_difference(rowindexes, list(range(colsize)))
        skipcols = colindexes if colIndexExclude else symmetric_difference(colindexes, list(range(rowsize)))

        for row in range(colsize):
            if row in skiprows: continue #skip given rows
            temprow = []
            for col in range(rowsize):
                if col in skipcols: continue #skip given columns
                cellvalue = str(sheet.cell(row + 1, col + 1).value)
                temprow.append(cellvalue)
            if not keepblankrows and isrowempty(temprow): continue
            outlist.append(temprow)
        return outlist
    
    def loadJson(filepath: str) -> dict:
        out:dict = {}
        with open(filepath, 'r', encoding='utf-8') as f:
        # Load the JSON data from the file
            #return json.load(f)
            data:dict = json.load(f)
            out = data.copy()
        return out
    
    #ai code
    def export_ll_to_xlsx(
        data: list[list[str]],
        filename: str,
        sheet_name: str = "Sheet1",
        header: list[str] = None,
        auto_adjust_column_width: bool = True
    ) -> bool:
        """
        Exports a list of lists to an Excel (.xlsx) file.

        Args:
            data (List[List[Any]]): The data to export, where each sublist is a row.
                                    Each item in the sublist will be a cell.
            filename (str): The name of the Excel file to create (e.g., "output.xlsx").
                            It will automatically add ".xlsx" if not present.
            sheet_name (str, optional): The name for the sheet in the workbook.
                                        Defaults to "Sheet1".
            header (Optional[List[str]], optional): A list of strings to use as the header row.
                                                    If None, no header is added. Defaults to None.
            auto_adjust_column_width (bool, optional): Whether to automatically adjust column widths
                                                    based on content. Defaults to True.

        Returns:
            bool: True if the export was successful, False otherwise.
        """
        try:
            

            # Ensure filename has .xlsx extension
            if not filename.lower().endswith(".xlsx"):
                filename += ".xlsx"

            # Create a new workbook and select the active sheet
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = sheet_name

            current_row_index = 1

            # Add header if provided
            if header:
                if not isinstance(header, list):
                    print("Error: Header must be a list of strings.")
                    return False
                sheet.append(header)
                current_row_index += 1

            # Write data rows
            for row_data in data:
                if not isinstance(row_data, list):
                    print(f"Warning: Skipping non-list row: {row_data}")
                    continue
                sheet.append(row_data)
                current_row_index += 1

            # Auto-adjust column widths if enabled
            if auto_adjust_column_width:
                for col_idx_plus_1, column_cells in enumerate(sheet.columns, 1): # sheet.columns is 0-indexed in iteration but we need 1-indexed for get_column_letter
                    max_length = 0
                    column_letter = get_column_letter(col_idx_plus_1)

                    for cell in column_cells:
                        if cell.value is not None:
                            try:
                                # Calculate length of the string representation of the cell value
                                cell_text_length = len(str(cell.value))
                                if cell_text_length > max_length:
                                    max_length = cell_text_length
                            except TypeError:
                                # Handle cases where str(cell.value) might fail for complex objects
                                # (though less likely if input is list[list[str]])
                                pass
                    
                    # Add a little padding to the width and set a minimum width
                    adjusted_width = (max_length + 2) if max_length > 0 else 8 # Default to 8 if column is empty or max_length is 0
                    if max_length > 0 and adjusted_width < 5: # Ensure a minimum for very short content
                        adjusted_width = 5
                    
                    sheet.column_dimensions[column_letter].width = adjusted_width


            workbook.save(filename)
            print(f"Excel file '{filename}' created successfully with sheet '{sheet_name}'.")
            return True
        
        except ImportError:
            print("Error: The 'openpyxl' library is not installed. Please install it using 'pip install openpyxl'.")
            return False
        except Exception as e:
            print(f"An error occurred during Excel export: {e}")
            return False

if __name__ == "__main__":
    excelpath = input("Enter the filepath of the data to read: ")
    
    data_ll_1 = ExcelPorter.loadExcelData_ll(excelpath, rowindexes=[0,1])
    data_ll_2 = ExcelPorter.loadExcelData_ll(excelpath, rowindexes=[0,1], colindexes=[0])
    data_ll_3 = ExcelPorter.loadExcelData_ll(excelpath, rowindexes=[0,1], colindexes=[0], rowIndexExclude=False)
    data_ll_4 = ExcelPorter.loadExcelData_ll(excelpath, rowindexes=[0,1], colindexes=[0], colIndexExclude=False)

    def printl(lst: list):
        for i in lst:
            print(i)

    printl(data_ll_1)
    print()
    printl(data_ll_2)
    print()
    printl(data_ll_3)
    print()
    printl(data_ll_4)
    print()
