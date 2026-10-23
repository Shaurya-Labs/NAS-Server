from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import utils.file_manager as file_manager
from flask_wtf.csrf import CSRFProtect
import json
import logging

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():

    app = Flask(__name__, template_folder="templates")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    logging.debug("Reading config.json for SECRET_KEY and ROOT_PATH")
    try:
        with open("./config/config.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.exception("Critical boot failure: config.json missing!")
        raise
        
    SECRET_KEY = data.get("SECRET_KEY", "")
    ROOT_PATH = data.get("ROOT_PATH", "")       #ROOT_PATH is the path where Home folder of NAS is to be created.
    
    if SECRET_KEY == "":
        logging.critical("App Boot Stopped: SECRET_KEY missing from config.json file!")
        raise RuntimeError("SECRET_KEY is not set!")
    elif ROOT_PATH == "":
        logging.critical("App Boot Stopped: ROOT_PATH missing from config.json file!")
        raise RuntimeError("ROOT_PATH is not set!")
    
    logging.debug("config.json read successfully")

    app.secret_key = SECRET_KEY

    logging.debug("Initializing SQLite database in flask app")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    db.init_app(app)
    csrf.init_app(app)
    logging.debug("SQLite database initialized successfully in flask app")

    logging.debug("Initializing flask login manager")
    flask_login_manager = LoginManager()
    flask_login_manager.init_app(app)
    flask_login_manager.login_view = "login"

    from models import User
    @flask_login_manager.user_loader
    def load_user(u_id):
        return User.query.get(int(u_id))
    logging.debug("flask login manager initialized successfully")
    
    logging.debug("Initializing Bcrypt in flask app")
    bcrypt = Bcrypt(app)
    logging.debug("Bcrypt initialized successfully in flask app")

    logging.debug("Registering routes in flask app")
    from routes import register_routes
    register_routes(app, bcrypt)
    logging.debug("Routes registered successfully in flask app")

    logging.debug("Initializing Migrage object of flask_migrate in flask app")
    migrate = Migrate(app, db)
    logging.debug("Migrate object of flask migrate initialized successfully in flask app")

    logging.debug("Making default folder structure in ROOT_PATH")
    file_manager.make_default_structure(ROOT_PATH)
    logging.debug("Default folder structure successfully made in ROOT_PATH")

    return app
