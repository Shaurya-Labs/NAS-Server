import json
from pathlib import Path
from flask import abort
import os
import logging

logging.debug("reading config.json file for ROOT_PATH")
with open("./config/config.json", "r") as f:
    ROOT_PATH = json.load(f).get("ROOT_PATH")
logging.debug("ROOT_PATH initialized successfully")

BASE_PATH = (Path(ROOT_PATH) / "Home").resolve()    #BASE_PATH is the path to the Home folder, which is the root folder NAS Server users can access.
TEMP_FOLDER_PATH = (Path(ROOT_PATH) / "temp").resolve()       #TEMP_FOLDER_PATH is the path to the temp folder, which NAS Server uses to store temp zip files to download(it's in the parent folder of the Home folder).
THUMBNAILS_PATH = (Path(ROOT_PATH) / "thumbnails").resolve()

CPP_UTILS_PATH = Path(__file__).parents[1] / "cpp_utils"

def check_and_get_secure_path(nas_path: str | Path) -> Path:
    """
    This function merges the nas_path passed with BASE_PATH, converts it to pathlib's Path object and returns it.
    This function also checks if the nas_path passed to the function is a child path of the NAS's Home directory
    path or the Home directory path itself or not.
    """

    target_path = Path(BASE_PATH / nas_path).resolve()

    try:
        target_path.relative_to(BASE_PATH)
    except ValueError:
        logging.warning(
            f"SECURITY VIOLATION: Directory traversal attempt blocked! "
            f"Input segment: '{nas_path}' tried to resolve to external path: '{target_path}'"
        )
        abort(403, description="Access Denied")

    return target_path

def validate_download_file_path(nas_file_path: str) -> dict[str, str | tuple[str, int] | None]:
        """
        This function checks if a nas_file_path passed to it is a valid path to a file or not(and within the Home directory)
        and returns a python dict the OS file_path, full OS file_directory path, filename and an error tuple which is not None
        if the filepath is invalid. 
        """
        file_path = check_and_get_secure_path(nas_file_path)       #Full OS path of file which the user requested to download.

        #Checking if the url tried to escape the root Home folder of NAS and tried to download an unauthorised file from the server.
        try:
            file_path.relative_to(BASE_PATH)
        except ValueError:
            return {
                "file_path": None,
                "file_directory": None,
                "filename": None,
                "error": ("Error: Access Denied", 403)
            }

        if not file_path.is_file():
            return {
                "file_path": None,
                "file_directory": None,
                "filename": None,
                "error": ("Error: File Not Found", 404)
            }

        filename = os.path.basename(file_path)
        file_directory = os.path.dirname(file_path)
        return {
            "file_path": file_path,
            "file_directory": file_directory,
            "filename": filename,
            "error": None
        }