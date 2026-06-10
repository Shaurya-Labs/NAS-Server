import os
from . import paths
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
import logging

def make_default_structure(path: str, folders: list[str]=["Images", "Videos", "Documents", "Temp"]) -> None:
    """
    This function creates a default structure of folders in the Home folder of the storage medium and also creates a temp folder for
    download zip files, in the parent folder of Home folder.
    'path' parameter is the path of the folder one level below the Home directory, if Home directory exists.
    folders parameter is the list of folders to be created inside the NAS Home folder.
    """
    
    home_path = os.path.join(path, "Home")
    temp_path = os.path.join(path, "temp")
    os.makedirs(home_path, exist_ok=True)
    os.makedirs(temp_path, exist_ok=True)
    for folder in folders:
        os.makedirs(os.path.join(home_path, folder), exist_ok=True)

def get_files_and_folder_structure(path: str) -> tuple[list[str], list[str], dict[str, float]]:
    """
    This function takes full OS path of the folder as parameter and returns a list of files, folders and dictionary where
    the file file name is the key and the file modified epoch time is the value.
    'path' is the path of the parent directory whose files and folder structure is to be determined.
    """
    file_map = {}
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file in files:
        file_map[file] = os.path.getmtime(os.path.join(path, file))
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    return files, folders, file_map

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

def cleanup_expired_temp_zips(zip_file_max_age: int) -> None:
    """
    This function deletes zip files from the temp folder, when they are older than ZIP_FILE_MAX_AGE seconds.
    """
    zip_files = os.listdir(paths.TEMP_FOLDER_PATH)
    now = datetime.now()
    zip_files_deleted = 0

    for zip_file in zip_files:
        str_download_time = zip_file.removeprefix("NAS Server download ").removesuffix(".zip")
        download_time = datetime.strptime(str_download_time, "%d-%m-%Y %H-%M-%S-%f")
        time_delta = now - download_time
        
        if time_delta.total_seconds() > zip_file_max_age:
            os.remove(os.path.join(paths.TEMP_FOLDER_PATH, zip_file))
            zip_files_deleted += 1
            logging.debug(f"Deleting expired zip file: {zip_file}")
        
    if zip_files_deleted == 0:
        logging.debug("No expired zip files found")
    else:
        logging.debug(f"Successfully deleted {zip_files_deleted} expired zip files")

def create_zip_file(nas_files_paths):
    current_datetime = datetime.now().strftime("%d-%m-%Y %H-%M-%S-%f")
    zip_file_name = f"NAS Server download {current_datetime}.zip"
    zip_file_path = Path(paths.TEMP_FOLDER_PATH / zip_file_name).resolve()

    #Creating a zip file containing all user requested files in the temp folder(TEMP_FOLDER_PATH).
    with ZipFile(zip_file_path, "w") as z:
        for nas_file_path in nas_files_paths:
            result = paths.validate_download_file_path(nas_file_path.lstrip("/"))
            if result["error"]:
                return result["error"]

            file_path = result["file_path"]
            filename = result["filename"]
            z.write(file_path, arcname=filename)

    return zip_file_path