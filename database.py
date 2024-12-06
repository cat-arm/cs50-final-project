from flask import Flask, abort, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from utils import hash_password, get_db

# Load environment variables from .env file
load_dotenv()

# get database url from .env file
DATABASE_URL = os.getenv("SUPABASE_URL")

if not DATABASE_URL:
    abort(404, description="SUPABASE_URL environment variable is not set in the .env file.")

# Get superadmin details from .env file
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD")
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL")

if not (SUPERADMIN_PASSWORD and SUPERADMIN_EMAIL):
    abort(404, description="Superadmin credentials are not set in the .env file.")

# create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}  # Ensures SSL connection for secure supabase need it
)

# Create a sessionmaker to manage database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ิbuilt models
Base = declarative_base()

def init_db():
    from models import Base, Role, User
    # Create a session to interact with the database
    db = SessionLocal()

    try:
        # Attempt to drop all existing tables (optional: can be commented out if not needed)
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables (if they don't exist)
        Base.metadata.create_all(bind=engine)

        # Predefine roles and their permissions
        roles = [
            Role(name="superadmin", permissions=["updateadmin"]),
            Role(name="admin", permissions=["ban"]),
            Role(name="user", permissions=["create_own_content", "update_own_content", "delete_own_content"])
        ]

        # Insert roles into the database
        db.add_all(roles)
        db.commit()

        # Create a superadmin user with hashed password
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        if not superadmin_role:
            return jsonify({"error": "Superadmin role not found in the database", "status_code": 404}), 404

        superadmin_user = User(
            first_name="Rithipong",  # should change this
            last_name="Leanghirunkun",  # should change this
            bio="superadmin",
            email=SUPERADMIN_EMAIL,
            password_hash=hash_password(SUPERADMIN_PASSWORD),  # Hash the password before saving
            role_id=superadmin_role.id
        )

        # Insert superadmin user into the database
        db.add(superadmin_user)
        db.commit()

        # Return a success message
        return jsonify({"message": "Drop old model table, new model table, all role data and superadmin created successfully!", "status_code": 200}), 200

    except IntegrityError as e:
        # Handle database integrity error (e.g., duplicate email, missing foreign key)
        db.rollback()  # Rollback the transaction
        return jsonify({"error": str(e.orig), "status_code": 500}), 500

    except ValueError as e:
        # Handle specific errors like "Superadmin role not found"
        db.rollback()  # Rollback the transaction
        return jsonify({"error": str(e), "status_code": 400}), 400

    except Exception as e:
        # Handle any other exceptions (e.g., general SQLAlchemy or unknown errors)
        db.rollback()  # Rollback the transaction
        return jsonify({"error": {"Something went wrong: " + str(e)}, "status_code": 500}), 500

    finally:
        db.close()  # Close the session when done

if __name__ == "__main__":
    app = Flask(__name__)
    with app.app_context():  # Push the app context before calling init_db
        init_db()