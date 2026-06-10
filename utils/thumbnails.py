from . import paths
import os
from PIL import Image, ImageOps
from io import BytesIO
import subprocess
import threading
import logging

# Image Thumbnails
def generate_image_thumbnail(image_path: str) -> tuple[BytesIO, str]:

    format_map = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP"
    }

    with open(image_path, "rb") as f:
        data = f.read()
    
    img_file_extension = os.path.splitext(image_path)[1].removeprefix(".").lower()
    img = Image.open(BytesIO(data))
    img = ImageOps.exif_transpose(img)      #Rotate the image according to the EXIF tag
    img.thumbnail((150, 150))

    buffer = BytesIO()      #would save image thumbnail to this temp buffer in memory
    img.save(buffer, format=format_map[img_file_extension])
    buffer.seek(0)

    mimetype = f"image/{img_file_extension}"
    return (buffer, mimetype)


# Video Thumbnails
def _cpp_thumbnail_generator_thread(files: str, videos_path: str, output_path: str):
        logging.debug("C++ thumbnail generator python thread started")

        cpp_exe_path = paths.CPP_UTILS_PATH / "thumbnail_generator.exe"
        command = [str(cpp_exe_path), videos_path, output_path]
        
        try:    
            result = subprocess.run(
                command,
                input=files,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8"
            )
            logging.info(f"C++ binary finished processing. Thumbnails successfully saved to: {output_path}")

        # If C++ code crashes
        except subprocess.CalledProcessError as e:
            logging.exception(f"C++ binary execution failed! Exit Code: {e.returncode}.\nError output:\n{e.stderr}")

        # If python code crashes
        except Exception:
            logging.exception("An unexpected Python runtime error occurred inside the thumbnail thread worker:")
        
def queue_thumbnail_generation(files_list: list[str], videos_path: str, output_path:str):
    logging.info("Generating thumbnails")
    
    cpp_exe_path = paths.CPP_UTILS_PATH / "thumbnail_generator.exe"
    if not cpp_exe_path.exists():
        logging.error("C++ binary 'thumbnail_generator.exe' not found.")
        raise FileExistsError(f"Native binary missing at: {cpp_exe_path}")

    # Removing video files names from files_list whose thumbnails already exists
    for file in files_list[:]:
        potentional_thumbnail_path = paths.THUMBNAILS_PATH / f"{file}.jpg"
        if potentional_thumbnail_path.exists():
            files_list.remove(file)

    files = "\n".join(files_list)
    logging.debug(f"Sending files to C++ stdin: \n{files}")

    # Only spawn background C++ worker if there are video files(whose thumbnails does not already exists) names in "files" variable
    if files != "":
        logging.debug("Starting C++ thumbnail generator python thread")
        thumbnail_generator_thread = threading.Thread(
            target=_cpp_thumbnail_generator_thread,
            args=(files, videos_path, output_path),
            daemon=True
        )
        thumbnail_generator_thread.start()

        logging.info("Thumbnail generation successfully handed off to background worker thread.")

    # If all videos(from files_list) thumbnails already exists, then do nothing    
    else:
        logging.debug("All thumbnails are already generated, no need to start C++ thumnail generator python thread")

    return True