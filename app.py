from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from file_manager import make_default_structure
from flask_wtf.csrf import CSRFProtect
import json

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():

    app = Flask(__name__, template_folder="templates")

    try:
        with open("./config/config.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError("config.json file not found.")
        
    SECRET_KEY = data.get("SECRET_KEY", "")
    ROOT_PATH = data.get("ROOT_PATH", "")       #ROOT_PATH is the path where Home folder of NAS is to be created.
    
    if SECRET_KEY == "":
        raise RuntimeError("SECRET_KEY is not set!")
    elif ROOT_PATH == "":
        raise RuntimeError("BASE_PATH is not set!")

    app.secret_key = SECRET_KEY

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    #app.config["SESSION_COOKIE_SECURE"] = True
    db.init_app(app)
    csrf.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    from models import User
    @login_manager.user_loader
    def load_user(u_id):
        return User.query.get(int(u_id))
    
    bcrypt = Bcrypt(app)

    from routes import register_routes
    register_routes(app, bcrypt)

    migrate = Migrate(app, db)
    make_default_structure(ROOT_PATH)
    return app