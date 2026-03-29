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

def get_files_and_folder_structure(home_path: str) -> tuple[list[str], list[str]]:
    """
    This function takes PATH of the folder as parameter and returns a list of files and folders respectively.
    'home_path' is the path of the Home directory.
    """

    files = [f for f in os.listdir(home_path) if os.path.isfile(os.path.join(home_path, f))]
    folders = [f for f in os.listdir(home_path) if os.path.isdir(os.path.join(home_path, f))]

    return files, folders