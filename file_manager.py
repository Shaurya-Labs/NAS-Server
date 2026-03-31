import os

def make_default_structure(path: str, folders: list[str]=["Images", "Videos", "Documents", "Temp"]) -> None:
    """
    This function creates a default structure of folders in the Home folder of the storage medium.
    'path' parameter is the path of the folder one level below the Home directory, if Home directory exists.
    """
    
    home_path = os.path.join(path, "Home")
    os.makedirs(home_path, exist_ok=True)
    for folder in folders:
        os.makedirs(os.path.join(home_path, folder), exist_ok=True)

def get_files_and_folder_structure(path: str) -> tuple[list[str], list[str]]:
    """
    This function takes PATH of the folder as parameter and returns a list of files and folders respectively.
    'path' is the path of the parent directory whose files and folder structure is to be determined.
    """

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    return files, folders

def resolve_filename_conflicts(filename: str, files_in_current_folder: list[str]) -> str:
    """
    This function checks if a file name(filename) already exists in files of current folder(files_in_current_folder), if True, then add a
    suitable increment suffix(eg: (1)) before extension to make a unique filename. If the increment suffix already exists, this function
    would increase the increment suffix value by 1.
    If the file name does not exists in file of current folder, then this function would return the original file name.
    """
    while filename in files_in_current_folder:
        middle = ""

        #Getting the staring name of the file, middle name (example: something.txt.html.py, middle name is .txt.html) and extension.
        if not filename.startswith("."):
            temp = filename.split(".")
            if len(temp) > 2:       #File name have middle name.
                middle = ".".join(temp[1:-1])
                middle = "." + middle
            name = temp[0].rstrip()
            ext = temp[-1]
            if name == ext:     #File name have no extension.
                ext = ""
            else:               #File name with a valid name and extension.
                ext = "." + ext
            str_to_resolve_conflicts = name
        else:       #If file name start with a period "."
            str_to_resolve_conflicts = filename
            ext = filename
            name = ""

        if str_to_resolve_conflicts.endswith(")") and "(" in str_to_resolve_conflicts:
        #Checking if the the file name already have an increment suffix (example: (1), (2)).
            if name:
                to_check_str = name.split("(")[-1]
            else:
                to_check_str = ext.split("(")[-1]
            to_check_str = to_check_str[0:-1]
            try:
                num = int(to_check_str)
                if name:
                    name = name[0 : len(name)-(len(to_check_str)+2)].rstrip()   #Removing the increment suffix from file name, to append our own.
                    filename = f"{name} ({num+1}){middle}{ext}"
                else:
                    ext = ext[0 : len(ext)-(len(to_check_str)+2)].rstrip()   #Removing the increment suffix from file extension, to append our own.
                    filename = f"{ext} ({num+1})"
            except ValueError:      #No valid integer inside the pair of parenthesis at the last of the file name.
                if name:
                    filename = f"{name.rstrip()} (1){middle}{ext}"
                else:
                    filename = f"{ext.rstrip()} (1)"
        else:
        #The file name had no valid increment suffix, so defining our own.
            if name:
                filename = f"{name.rstrip()} (1){middle}{ext}"
            else:
                filename = f"{ext.rstrip()} (1)"
    return filename