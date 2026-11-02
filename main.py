from excelporter import ExcelPorter
from reformatter import Reformatter
import os
import sys

################ P L A N ################

""" ---<<< REFORMATTER >>>---

    --<< Version 0 >>--
        X  has prod-level working functionality

    --<< Version 1 >>--
        O lookuptable implementation
            - not in V0 as not needed for newer exports
        O type casting values as what they are supposed to be

    --<< Version 2 >>--
        O add Proper error detection and raising
    
    --<< Version 3 >>--
        O run performance checks
            O locate bottlenecks and optimize

    -< additional notes >-
        - it is the heart and brain of the program
"""

""" ---<<< GUI >>>---

    --<< Version 0 >>--
        O prompt for path strings in console

    --<< Version 1 >>--
        O create tkinter popup
            prompt for; input data, output path

    --<< Version 2 >>--
        O create configurable "datagrabbers"/sections of data to grab 
            - (editing config file in program)

    < additional notes>
        - ease of use/user experience
"""

"""---- <<<< Main Functionality >>>> ----
    --<< Version 0 >>--
     - workable for those with: 
       intermediate technical knowledge and 
       advanced knowledge of the program
    O has V0 for <GUI> and <REFORMATTER>

    --<< Version 1 >>--
     - workable for those with: 
       beginner technical knowledge and 
       intermediate knowledge of the program
    O has V1 for <GUI> and V2 for <REFORMATTER>

    --<< Version 2 >>--
     - workable for those with: 
       beginner technical knowledge and 
       beginner knowledge of the program
    O has V2 for <GUI> and V3 for <REFORMATTER>
    
    < additional notes>
        - this is to be the data reformatter to end all data reformatters,
          though, surely k2 will not invent a better idiot and make this
          null and void 😂😂😂😐
"""

################ P L A N ################


# put tkinter gui here
def get_base_path():
    """ Get absolute path to the executable or script directory. """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # For finding files *next to the executable*, we need its actual directory
        return os.path.dirname(sys.executable)
    else:
        # Not bundled, running in development (e.g., from VS Code)
        # This will be the directory of the script
        return os.path.dirname(os.path.abspath(__file__))


def get_filename(path: str) -> str:
    i1 = len(path) - path[::-1].index("\\")
    i2 = len(path) - path[::-1].index(".") - 1
    return path[i1:i2]

def get_extension(path: str) -> str:
    i1 = len(path) - path[::-1].index(".")
    return path[i1:]

def get_folder(path: str) -> str:
    i1 = len(path) - path[::-1].index("\\") - 1
    return path[:i1]

def add_string_to_filename_in_filepath(path:str, string_to_add:str) -> str:
    folderpath = get_folder(path)
    oldfilename = get_filename(path)
    oldextension = get_extension(path)
    return folderpath + "\\" + oldfilename + string_to_add + "." + oldextension



def select_listitem(filelist: list[str], prompt_text: str) -> str:
    while True:
        length:int = max([len(string) for string in filelist])
        dataselectiondict:dict = {k + 1:v for k, v in enumerate(filelist)}
        file_options = "\n\n"
        for key, filename in dataselectiondict.items():
            file_options += f"{filename.rjust(length, " ")} : {key}\n"
        rawfile_selection = input(file_options + prompt_text)
        try:
            return dataselectiondict[int(rawfile_selection)]
        except: print("\nEnter a valid selection.")
def temporary_run_function(export:bool = True):

    base_dir = get_base_path()

    # Get the absolute path of the currently executing script
    script_path = os.path.abspath(__file__)
    # Get the directory containing the script
    script_dir = os.path.dirname(script_path)
    # List all entries (files and directories) in the script's directory
    all_entries = []
    try:
        all_entries = os.listdir(base_dir)
    except FileNotFoundError:
        input(f"Error: Directory not found: {base_dir}. Press Enter to exit.")
        return
    except Exception as e:
        input(f"Error listing directory {base_dir}: {e}. Press Enter to exit.")
        return
    
    excelfiles = []
    configfiles = []
    for entry in all_entries:
        full_path = os.path.join(base_dir, entry)
        if os.path.isfile(full_path):
            if full_path.endswith(".xlsx"):
                excelfiles.append(entry)
            elif full_path.endswith(".json"):
                configfiles.append(entry)
    if configfiles == []:
        input("No config files found in local directory. Exiting.")
        return

    if excelfiles == []:
        input("No excel files found in local directory. Exiting.")
        return

    configselection = select_listitem(configfiles, "Enter the number corresponding to the config file to read from: ")
    
    configpath = os.path.join(base_dir, configselection)

    dataselection = select_listitem(excelfiles, "Enter the number corresponding to the file you would like to reformat: ")
    rawdatapath = os.path.join(base_dir, dataselection) 

    outputpath = input("\n>>> Leave blank to put the reformatted file in the same directory \
with the default text added to the original filepath\n>>> OR Give a name to add to the end of reformatted \
file, placed in the same directory as the original filepath)\n>>> OR Enter the path to the output folder: ")
    
    testmode_input = input("\n ...Press Enter to reformat file... ")

    if ":" not in outputpath:
        if outputpath == "":
            outputpath = add_string_to_filename_in_filepath(rawdatapath, " - reformatted")
        else:
            outputpath = add_string_to_filename_in_filepath(rawdatapath, outputpath)

    testmode = False
    if testmode_input.upper() == "TESTMODE":
        testmode = True

    data:list[list[str]] = None

    data = ExcelPorter.loadExcelData_ll(rawdatapath, rowindexes = []) # uncomment above and comment this

    configdict = ExcelPorter.loadJson(configpath)
    reformatter = Reformatter(configdict, testmode=testmode)

    reformatter.preprocess_data(data)

    reformatter.load_data(data)

    reformatted = reformatter.reformat()

    if export:
        ExcelPorter.export_ll_to_xlsx(reformatted, outputpath)
    
    input("\nFile Reformatted.\n  ...Press enter to close...")



if __name__=="__main__":

    
    temporary_run_function()

