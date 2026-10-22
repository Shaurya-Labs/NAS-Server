from . import paths
from . import cpp_worker_handler
import os
from PIL import Image, ImageOps
from io import BytesIO
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
def queue_thumbnail_generation(files_list: list[str], videos_path: str, output_path:str):
    logging.info("Generating thumbnails")

    # Removing video files names from files_list whose thumbnails already exists
    for file in files_list[:]:
        potentional_thumbnail_path = paths.THUMBNAILS_PATH / f"{file}.jpg"
        if potentional_thumbnail_path.exists():
            files_list.remove(file)

    files = "\n".join(files_list)

    # Only spawn background C++ worker if there are video files(whose thumbnails does not already exists) names in "files" variable
    if files != "":
        logging.debug(f"Would send these files to C++ stdin: \n{files}")
        cpp_worker_handler.cpp_worker("thumbnail_generator.exe", files, [videos_path, output_path])

    # If all videos(from files_list) thumbnails already exists, then do nothing
    else:
        logging.debug("All thumbnails are already generated, no need to start C++ thumnail generator python thread")

    return True