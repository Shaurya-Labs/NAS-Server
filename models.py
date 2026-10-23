from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):

    __tablename__ = "users"
    
    u_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"User ID: {self.u_id}, Username: {self.username}"
    
    def get_id(self):
        return self.u_id