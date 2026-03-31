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

with open("./config/config.json", "r") as f:
    ROOT_PATH = json.load(f).get("ROOT_PATH")

ROOT_PATH = Path(ROOT_PATH).resolve()
BASE_PATH = Path(ROOT_PATH / "Home").resolve()    #BASE_PATH is the path to the Home folder which NAS Server can access.
login_attempts = {} #Convert it to json files latter.
timed_out_ips = {}  #Connvert it to json files latter.

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
            should_login, data = login_manager.authenticate_user(User, request, bcrypt)
            if should_login:
                login_user(data)
                return redirect(url_for("nas_home"))
            else:
                return data
    
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
        else:               #if nas_folder_path is not an empty string, then it means that the user wants to access a sub folder inside the root Home folder.
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
        return render_template("NAS_Storage.html", files=files, folders=folders, current_folder_path=nas_folder_path, thumbnail=thumbnail)


    """
    nas_file_path is the path used for navigating NAS files in Home folder's child folders, it's a child path in Home folder,
    it does not start with 'Home/' because the BASE_PATH already ends with the Home folder path.
    """
    @app.route("/download/<path:nas_file_path>")
    @login_required
    def download(nas_file_path: str):
        file_path = os.path.join(BASE_PATH, nas_file_path)       #Path of file which the user requested to download.

        #Checking if the url tried to escape the Home folder of NAS
        file_path = Path(file_path).resolve()

        if not file_path.is_file():
            return "Error: File Not Found", 404

        #Checking if the url tried to escape the root Home folder of NAS and tried to download an unauthorised file from the server.
        try:
            file_path.relative_to(BASE_PATH)
        except ValueError:
            return "Error: Access Denied", 403
        
        filename = os.path.basename(file_path)
        file_directory = os.path.dirname(file_path)
        return send_from_directory(file_directory, filename, as_attachment=True)
    
    @app.route("/upload", methods=["POST"])
    @login_required
    def upload():
        files = request.files.getlist("files")
        current_nas_folder_path = request.form.get("current_folder_path")
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