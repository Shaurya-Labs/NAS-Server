from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from models import User
from flask_bcrypt import Bcrypt
from file_manager import get_files_and_folder_structure, resolve_filename_conflicts
import os
from pathlib import Path
from auth import login_manager
import json
from zipfile import ZipFile
from datetime import datetime

with open("./config/config.json", "r") as f:
    ROOT_PATH = json.load(f).get("ROOT_PATH")

ROOT_PATH = Path(ROOT_PATH).resolve()
BASE_PATH = Path(ROOT_PATH / "Home").resolve()    #BASE_PATH is the path to the Home folder, which is the root folder NAS Server users can access.
TEMP_FOLDER_PATH = Path(ROOT_PATH / "temp").resolve()       #TEMP_FOLDER_PATH is the path to the temp folder, which NAS Server uses to store temp zip files to download(it's in the parent folder of the Home folder).

def register_routes(app: Flask, bcrypt: Bcrypt):

    @app.route("/")
    def index():
        return render_template("index.html")

    """
    @app.route("/create_new_user", methods=["GET", "POST"])
    @login_required
    def create_new_user():
        if request.method == "GET":
            return render_template("create_new_user.html")
        elif request.method == "POST":
            data = request.form
            username = data.get("username")
            password = data.get("password")
            pw_hash = bcrypt.generate_password_hash(password)
            user = User(username=username, password=pw_hash)
            db.session.add(user)
            db.session.commit()
            return "You're successfully signed up
     """
        
    @app.route("/login", methods=["GET", "POST"])
    def login():

        if request.method == "GET":
            return render_template("login.html")
        
        elif request.method == "POST":
            """
            user_or_message variable is there becuase the authenticate_user() fuction returns False and an error message if login fails
            and if login succeeds, then it returns True and the user object to login.
            """
            should_login, user_or_message = login_manager.authenticate_user(User, request, bcrypt)
            if should_login:
                login_user(user_or_message)
                return redirect(url_for("nas_home"))
            else:
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
        thumbnail = None
        if nas_folder_path:        #if nas_folder_path is empty string, then it means the user wants to access a sub folder inside the root Home folder.
            target_path = BASE_PATH / nas_folder_path
        else:                      #if nas_folder_path is not an empty string, then it means that the user wants to access a sub folder inside the root Home folder.
            target_path = BASE_PATH

        images_path = BASE_PATH / "Images"
        videos_path = BASE_PATH / "Videos"
        
        #Checking if the url tried to escape the Home folder of NAS and tried to access an unauthorised folder of the server.
        target_path = Path(target_path).resolve()
        try:
            target_path.relative_to(BASE_PATH)
        except ValueError:
            return "Error: Access Denied", 403
        
        #Displaying the thumbnails of images only inside 'Images' folder(iamge_path) and vidoes as a video player only inside 'Vidoes' folder(videos_path).
        if target_path == images_path:
            thumbnail = "images"
        elif target_path == videos_path:
            thumbnail = "videos"
        
        files, folders = get_files_and_folder_structure(target_path)
        return render_template("NAS_Storage.html", files=files, folders=folders, current_nas_folder_path=nas_folder_path, thumbnail=thumbnail)

    @app.route("/download", methods=["POST"])
    @login_required
    def download():

        def validate_file_path(nas_file_path: str) -> dict[str, str | tuple[str, int] | None]:
            """
            This function checks if a nas_file_path passed to it is valid or not and returns a python dict the OS file_path,
            OS file_directory, filename and an error tuple if the filepath is not valid. 
            """
            file_path = Path(BASE_PATH / nas_file_path).resolve()       #Full OS path of file which the user requested to download.

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

        nas_files_path: list[str] = request.form.getlist("filename")     #nas_files_path is the python list of nas_file_path paths to downlaod.

        if len(nas_files_path) == 1:        #If the user request to downloaded only one file(nas_files_path list only have one nas_file_path).        
            result = validate_file_path(nas_files_path[0].lstrip("/"))
            if result["error"]:
                return result["error"][0], result["error"][1]

            file_directory = result["file_directory"]
            filename = result["filename"]

            #as_attachment = request.args.get("as_attachment").lower() == "true"     #If it's video file in 'Home/Videos' folder, then as_attachment=True, otherwise as_attachment=False.
            return send_from_directory(file_directory, filename)

        else:                               #If the user requested to downloaded multiple files(nas_files_path list have multiple nas_file_path).
            current_datetime = datetime.now().strftime("%d-%m-%Y %H-%M-%S-%f")
            zip_file_name = f"NAS Server download {current_datetime}.zip"
            zip_file_path = Path(TEMP_FOLDER_PATH / zip_file_name).resolve()

            #Creating a zip file containing all user requested files in the temp folder(TEMP_FOLDER_PATH).
            with ZipFile(zip_file_path, "w") as z:
                for nas_file_path in nas_files_path:
                    result = validate_file_path(nas_file_path.lstrip("/"))
                    print(result)
                    if result["error"]:
                        print("returning")
                        return result["error"][0], result["error"][1]

                    file_path = result["file_path"]
                    file_directory = TEMP_FOLDER_PATH
                    filename = result["filename"]
                    print(file_path)
                    z.write(file_path, arcname=filename)

            return send_from_directory(TEMP_FOLDER_PATH, zip_file_name)
        
    @app.route("/media/<path:nas_file_path>")
    @login_required
    def media(nas_file_path):
        file_path = Path(BASE_PATH / nas_file_path).resolve()

        #Checking if the url tried to escape Home folder of NAS.
        try:
            file_path.relative_to(BASE_PATH)
        except ValueError:
            return "Access Denied", 403
        
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
        
    @app.route("/thumbnail/<path:nas_file_path>")
    @login_required
    def thumbnail(nas_file_path):
        file_path = Path(BASE_PATH / nas_file_path).resolve()

        #Checking if the url tried to escape Home folder of NAS.
        try:
            file_path.relative_to(BASE_PATH)
        except ValueError:
            return "Access Denied", 403
        
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload():
        files = request.files.getlist("files")
        current_nas_folder_path = request.form.get("current_nas_folder_path")
        upload_folder_path = (BASE_PATH / current_nas_folder_path).resolve()

        files_in_current_folder, _ = get_files_and_folder_structure(upload_folder_path)
    
        #Checking if the url tried to escape Home folder of NAS.
        try:
            upload_folder_path.relative_to(BASE_PATH)
        except ValueError:
            return "Access Denied", 403
        
        #Resolving file name conflicts(if any) of all the uploaded files.
        for file in files:
            filename = file.filename
            if filename == "":
                continue

            elif filename in files_in_current_folder:
                filename = resolve_filename_conflicts(filename, files_in_current_folder)
                files_in_current_folder.append(filename)

            file.save(upload_folder_path / filename)
        return redirect(url_for("nas_home", nas_folder_path=current_nas_folder_path))

    @app.route("/create_folder", methods=["POST"])
    @login_required
    def create_folder():
        data = request.form
        current_nas_folder_path = data.get('current_nas_folder_path')
        new_folder_name = data.get('new_folder_name')
        new_folder_path = Path(BASE_PATH / current_nas_folder_path / new_folder_name).resolve()

        #Checking if the url tried to escape Home folder of NAS.
        try:
            new_folder_path.relative_to(BASE_PATH)
        except ValueError:
            return "Error: Access Denied", 403
        
        os.makedirs(new_folder_path, exist_ok=True)
        return redirect(url_for("nas_home", nas_folder_path=current_nas_folder_path))
    
    @app.route("/delete", methods=["POST"])
    @login_required
    def nas_delete():
        files_nas_path: list[str] = request.get_json()
        print(files_nas_path)
        
        for file_nas_path in files_nas_path:
            file_nas_path = file_nas_path.lstrip("/")
            print(file_nas_path)
            file_path = Path(BASE_PATH / file_nas_path).resolve()
            print(file_path)

            #Checking if the url tried to escape Home folder of NAS.
            try:
                file_path.relative_to(BASE_PATH)
            except ValueError:
                return "Access Denied", 403
            os.remove(file_path)
            
        return {"status": "ok"}