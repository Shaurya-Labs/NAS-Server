from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from folder_structure import make_default_structure

db = SQLAlchemy()

def create_app():

    app = Flask(__name__, template_folder="templates")
    app.secret_key = "Very Secret hehe asdopf h98p3w eyhfuoihas"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User
    @login_manager.user_loader
    def load_user(u_id):
        return User.query.get(int(u_id))
    
    bcrypt = Bcrypt(app)

    from routes import register_routes
    register_routes(app, db, bcrypt)

    migrate = Migrate(app, db)
    make_default_structure(r"C:\Users\Shaur\Desktop\Projects\NAS-Server\NAS_Files")
    return app