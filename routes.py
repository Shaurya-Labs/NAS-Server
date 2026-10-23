from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from flask_bcrypt import Bcrypt
from auth import login_manager
from utils import paths, ui_helpers, file_manager, thumbnails
from pathlib import Path
import logging
import os

def register_routes(app: Flask, bcrypt: Bcrypt):

    # This function would run before every request to the server from client and would log the request
    @app.before_request
    def log_every_single_request():
        # Exclude static assets
        if not request.path.startswith('/static'):
            logging.info(f"Network Hit: {request.method} {request.path} from IP {request.remote_addr}")


    @app.route("/")
    def index():

        # Redirect the user to the login page, if the user is not already logged in
        # and have visited the homepage of the site, if the user is already logged in
        # then redirect the user to the home page
        if current_user.is_authenticated:
            # return render_template("index.html")
            return redirect(url_for("Home"))
        else:
            return redirect(url_for("login"))
    

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        
        elif request.method == "POST":
            """
            user_or_message variable is there becuase the authenticate_user() fuction returns False and an error message if login fails
            and if login succeeds, then it returns True and the user object to login.
            """
            logging.info("authenticating user")
            should_login, user_or_message = login_manager.authenticate_user(User, request, bcrypt)
            if should_login:
                login_user(user_or_message)
                logging.info("user authenticated and logged in successfully")
                return redirect(url_for("nas_home"))
            else:
                logging.error("user authentication failed")
                return user_or_message


    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))
    
    #This is the NAS Server's Home directory route.
    """
    nas_folder_path is the path used for navigating NAS folders inside Home folder, it's a child path in Home folder,
    it does not start with 'Home/' folder because the BASE_PATH already ends with the Home folder path.
    """
    @app.route("/Home/", defaults={"nas_folder_path": ""})
    @app.route("/Home/<path:nas_folder_path>")
    @login_required
    def nas_home(nas_folder_path):

        target_path = paths.check_and_get_secure_path(nas_folder_path)
        files_per_page = 100

        logging.debug(f"Loading NAS storage view for target path: '{target_path}'")
        thumbnail = ui_helpers.get_thumbnail_type(target_path)
        files, folders, file_map = file_manager.get_files_and_folder_structure(target_path)

        #Generate and check video thumbnails if user is in video path
        if thumbnail == "videos":
            files_per_page = files_per_page // 4
            logging.debug("Videos folder access detected, generating videos thumbnails")
            thumbnails.queue_thumbnail_generation(files, target_path, paths.THUMBNAILS_PATH)

        #sort the files from newly modified to older modified
        sorted_file_map = dict(sorted(file_map.items(), key=lambda x: x[1], reverse=True))
        sorted_files = list(sorted_file_map.keys())

        current_page = request.args.get("page", default=1, type=int)
        start_index, end_index, display_nav_btns = ui_helpers.handle_files_container_navigation(current_page, files_per_page, len(sorted_files))

        return render_template("NAS_Storage.html", 
                               files=sorted_files[start_index:end_index],
                               folders=folders,
                               current_nas_folder_path=nas_folder_path,
                               thumbnail=thumbnail,
                               display_nav_btns = display_nav_btns
        )
    

    @app.route("/download", methods=["POST"])
    @login_required
    def download():
        ZIP_FILE_MAX_AGE = 172800       #Number of seconds after which the zip file(from the download temp folder) would be deleted

        nas_files_paths: list[str] = request.form.getlist("nasFilePath")    #nas_files_path is the python list of nas_file_path paths to downlaod.
        logging.info(f"User requested to download {len(nas_files_paths)} file(s), processing the download.")

        logging.debug("Deleting expired zip files")
        file_manager.cleanup_expired_temp_zips(ZIP_FILE_MAX_AGE)
        logging.debug("Expired zip files cleanup completed")

        if len(nas_files_paths) == 1:        #If the user request to downloaded only one file(nas_files_path list only have one nas_file_path).        
            result = paths.validate_download_file_path(nas_files_paths[0].lstrip("/"))
            if result["error"]:
                logging.error(f"File not sent for download, Error: {result["error"]}")
                return result["error"][0], result["error"][1]

            file_directory = result["file_directory"]
            filename = result["filename"]

            #as_attachment = request.args.get("as_attachment").lower() == "true"     #If it's video file in 'Home/Videos' folder, then as_attachment=True, otherwise as_attachment=False.
            logging.info(f"Sending file {filename} for download for download")
            return send_from_directory(file_directory, filename, as_attachment=True)

        else:                       #If the user requested to downloaded multiple files(nas_files_path list have multiple nas_file_path).
            result = file_manager.create_zip_file(nas_files_paths)
            if isinstance(result, tuple):    # result variable contains the error code and error message if create_zip_file function tried to raise an error.
                logging.error(f"Files not sent for download, Error: {result}")
                return result[0], result[1]
            elif isinstance(result, Path):  # result variable contains the path to the newly made zip file for the user to downlaod if everything went right.
                zip_filename = os.path.basename(result)
                logging.info(f"Sending server made zip {zip_filename} for download")
                return send_from_directory(paths.TEMP_FOLDER_PATH, zip_filename)


    @app.route("/thumbnail/<path:nas_file_path>")
    @login_required
    def thumbnail(nas_file_path):
        file_path = paths.check_and_get_secure_path(nas_file_path)
        file_extension = file_path.suffix
        
        # return image files thumbnails
        if file_extension in [".jpg", ".png", ".jpeg", ".webp"]:
            image_buffer, mimetype = thumbnails.generate_image_thumbnail(file_path)    
            return send_file(image_buffer, mimetype=mimetype)
        
        # return video files thunbnails
        elif file_extension in [".mp4", ".mkv", ".mov", ".webm"]:
            video_thumbnail_filename = f"{file_path.name}.jpg"
            video_thumbnail_path = paths.THUMBNAILS_PATH / video_thumbnail_filename

            if video_thumbnail_path.exists():
                return send_file(video_thumbnail_path, mimetype="image/jpeg")
            else:
                # logging.debug(f"JS requested for thumbnail '{video_thumbnail_filename}' which was NOT FOUND!")    This line is commented so that it doesn't spam in the logs when the browser polls, only uncomment it during debugging
                return "Thumbnail is being processed", 202

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload():
        files = request.files.getlist("files")
        current_nas_folder_path = request.form.get("current_nas_folder_path")
        upload_folder_path = paths.check_and_get_secure_path(current_nas_folder_path)

        uploaded_filenames = [file.filename for file in files]
        if uploaded_filenames[0] != "":     # Only execute the if block if the user clicked the upload button after selecting files.
            logging.info(
                    f"User uploading {len(files)} file(s) "
                    f"to NAS path '/Home/{current_nas_folder_path}': {uploaded_filenames}"
            )

        files_in_current_folder = file_manager.get_files_and_folder_structure(upload_folder_path)[0]

        # Resolving file name conflicts(if any) of all the uploaded files.
        for file in files:
            filename = file.filename
            if filename == "":
                continue

            elif filename in files_in_current_folder:
                filename = file_manager.resolve_filename_conflicts(filename, files_in_current_folder)
                files_in_current_folder.append(filename)

            logging.debug(f"Saving file: {filename} to path: {upload_folder_path}")
            file.save(upload_folder_path / filename)
            logging.debug(f"File: {filename} saved successfully to path: {upload_folder_path}")
        return "Files uploaded successfully!", 200

    @app.route("/delete", methods=["POST"])
    @login_required
    def nas_delete():
        nas_files_path: list[str] = request.get_json()
        logging.info(f"User requested to delete {len(nas_files_path)} file(s):\n- " +
                     "\n- ".join(nas_files_path)
                     )
    
        for nas_file_path in nas_files_path:
            nas_file_path = nas_file_path.lstrip("/")
            file_path_to_delete = paths.check_and_get_secure_path(nas_file_path)

            logging.debug(f"Deleting file: {file_path_to_delete}")
            os.remove(file_path_to_delete)
            logging.debug(f"File: {file_path_to_delete} deleted successfully")

        return {"status": "ok"}


    @app.route("/create_folder", methods=["POST"])
    @login_required
    def create_folder():
        data = request.form
        current_nas_folder_path = data.get('current_nas_folder_path')
        new_folder_name = data.get('new_folder_name')
        new_folder_path = paths.check_and_get_secure_path(os.path.join(current_nas_folder_path, new_folder_name))

        logging.info(f"User requested to create a new folder, creating new folder(if not already exists) at path: {new_folder_path}")

        os.makedirs(new_folder_path, exist_ok=True)
        logging.debug(f"New folder created successfully(if not already existed) at path: {new_folder_path}")
        return redirect(url_for("nas_home", nas_folder_path=current_nas_folder_path))       


    # This route sends the video or image file to play or show them directly in browser
    @app.route("/media/<path:nas_file_path>")
    @login_required
    def media(nas_file_path):
        logging.info(f"User requested to watch: {nas_file_path} media directly in their browser.")
        file_path = paths.check_and_get_secure_path(nas_file_path)
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
