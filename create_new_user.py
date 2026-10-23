from app import create_app, db
from models import User
from flask_bcrypt import Bcrypt

app = create_app()

with app.app_context():
    bcrypt = Bcrypt(app)
    
    username = "default" 
    password = "default"

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=hashed_pw)

    db.session.add(user)
    db.session.commit()

    print("New user added successfully")
