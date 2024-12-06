# utils.py
import os
import re
from passlib.context import CryptContext
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
from sqlalchemy.orm import joinedload, sessionmaker, Session as DBSession
from werkzeug.exceptions import Unauthorized

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mysecretkey")  # Secret key for sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_PERMANENT'] = True  # Session should last even after browser is closed
Session(app)  # Initialize session management

# Dependency to get the database session 
def get_db():
    from database import engine
    # Create a sessionmaker to manage database sessions
    # SQLAlchemy will not sent auto commit, no saveing to buffer when query, bind session to engin tell session where is the database to connect
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()

# Function to validate email format
def is_valid_email(email: str):
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None

def is_valid_password(password: str):
    password_regex = r'^(?=.*[A-Z])(?=.*[!@#$%^&*()_+?|])(?=.{8,})'
    return re.match(password_regex, password) is not None

# Hash the password 
def hash_password(password: str):
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.hash(password)  # hashes and salts the password

def check_password(plain_password: str, stored_hash: str):
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    if not pwd_context.verify(plain_password, stored_hash):
        return False
    return True

def get_current_user():
    from models import User
    user_id = session.get("user_id")
    if not user_id:
        return None

    db: Session = next(get_db())
    user = (
        db.query(User)
        .options(joinedload(User.role))  # Eagerly load the role relationship
        .filter(User.id == user_id)
        .first()
    )
    db.close()  # Close the session after fetching the user
    return user

def check_permission(user, permission):
    role = user.role
    return permission in role.permissions

def handle_error(error_message):
    return render_template("error.html", message=error_message)
