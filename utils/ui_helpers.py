from . import paths
from pathlib import Path

def get_thumbnail_type(target_path: str | Path):
    thumbnail = None
    images_path = paths.BASE_PATH / "Images"
    videos_path = paths.BASE_PATH / "Videos"

    target_path = paths.check_and_get_secure_path(target_path)

    #Displaying the thumbnails of images only inside 'Images'(images_path) folder(or it's subfolder) and vidoes as a video player only inside 'Vidoes'(videos_path) folder(or it's subfolder).
    try:
        target_path.relative_to(images_path)
        thumbnail = "images"
    except ValueError:
        pass
    try:
        target_path.relative_to(videos_path)
        thumbnail = "videos"
    except ValueError:
        pass

    return thumbnail

def handle_files_container_navigation(current_page, files_per_page, length_sorted_files):
    #logic for next and previous buttons
        display_nav_btns = False
        if current_page <= 0:
            current_page = 1
        start_index = ((current_page-1)*files_per_page)
        end_index = (start_index+files_per_page)
        if length_sorted_files > files_per_page:
            display_nav_btns = True
        
        return start_index, end_index, display_nav_btns