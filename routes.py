from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from models import User
from flask_bcrypt import Bcrypt
from folder_structure import get_files_and_folder_structure
import os

def register_routes(app: Flask, db: SQLAlchemy, bcrypt: Bcrypt):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():

        if request.method == "GET":
            return render_template("signup.html")
        elif request.method == "POST":
            data = request.form
            username = data.get("username")
            password = data.get("password")
            pw_hash = bcrypt.generate_password_hash(password)
            user = User(username=username, password=pw_hash)
            db.session.add(user)
            db.session.commit()
            return "You're successfully signed up"
        
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        elif request.method == "POST":
            data = request.form
            username = data.get("username")
            password = data.get("password")
            matched_user = User.query.filter(User.username == username).first()
            
            if matched_user is None:
                return "Incorrect Username"
            else:
                if bcrypt.check_password_hash(matched_user.password, password):
                    login_user(matched_user)
                    return "Logged In Successfully!!"
                else:
                    return "Incorrect Password"
        
    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))
    
    #This is the NAS Server's Home directory path
    @app.route("/home/", defaults={"nas_path": ""})
    @app.route("/home/<path:nas_path>")
    @login_required
    def nas_home(nas_path):
        base_path = r"C:\Users\Shaur\Desktop\Projects\NAS-Server\NAS_Files\Home"
        if nas_path:
            target_path = os.path.join(base_path, nas_path)
        else:
            target_path = base_path

        files, folders = get_files_and_folder_structure(target_path)
        return render_template("NAS_Storage.html", files=files, folders=folders, current_path=nas_path)