import os
from datetime import timedelta, datetime, timezone
from flask import Flask, request, jsonify, render_template, session, redirect
from flask_session import Session  # Used for session management
from sqlalchemy.orm import Session as DBSession
from dotenv import load_dotenv
from models import Role, User, Content
from utils import is_valid_password, is_valid_email, hash_password, check_password
from database import get_db


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mysecretkey")  # Secret key for sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_PERMANENT'] = True # Session should last even after browser is closed

Session(app)  # Initialize session management

@app.route("/")
def index():
    db: Session = next(get_db())
    contents = db.query(Content).filter(Content.status != "Inactive").all()
    contents_list = [{"id": content.id, "quote": content.quote} for content in contents]
    print("Contents listed successfully")
    return jsonify(contents_list)

@app.route("/session", methods=["GET"])
def check_session():
    user_id = session.get("user_id")
    if user_id:
        return jsonify({"message": f"User is logged in with ID {user_id}"})
    return jsonify({"message": "No user is logged in"}), 401

@app.route("/login", methods=["POST"])
def login():
    # get data from the form
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required", "status_code": 404}), 404

    # Check if the email exists in the database
    db: DBSession = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    # check_password is a custom function
    if user and check_password(password, user.password_hash):
        session.permanent = True
        # Store user ID in session
        session["user_id"] = user.id

        # Set session expiry (30 days)
        app.permanent_session_lifetime = timedelta(days=30)
        print("login successful")
        return redirect("/")
    return jsonify({"error": "Invalid credentials", "status_code": 401}), 401

@app.route("/logout", methods=["POST"])
def logout():
    # Clear session data
    session.clear()
    print("logout successful")
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    # Get data from the form
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    bio = request.form.get("bio", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    password_confirm= request.form.get("password_confirm", "").strip()

    # Check valid pasword
    if not is_valid_password(password):
        return jsonify({
            "error": "Password must be at least 8 characters long, contain at least one uppercase letter, and one special character", 
            "status_code": 400
        }), 400
    
    # Check password and confirmation password match
    if not password == password_confirm:
        return jsonify({"error": "Your password and confirmation password did not match", "status_code": 400}), 400

    # Check required field
    if not all([first_name, last_name, email, password]):
        return jsonify({"error": "All fields are required", "status_code": 400}), 400

    # check valid email
    valid_email = is_valid_email(email)
    if not valid_email:
        return jsonify({"error": "Email is invalid pattern", "status_code": 400}), 400
    
    #hash password
    password_hash = hash_password(password)

    # Get the database session
    db: DBSession = next(get_db())

    try:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
             return jsonify({"error": "This email is already registered", "status_code": 400}), 400
        
        # Get the role object where name is user
        role = db.query(Role).filter(Role.name == "user").first()

        # Check if the role exists
        if not role:
            return jsonify({"error": "Role user was not found", "status_code": 404}), 404

        # Create a new user with the role
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            bio=bio,
            email=email,
            password_hash=password_hash,
            role_id=role.id  # Assigning the user the user role
        )

        # Add the user to the session and commit
        db.add(new_user)
        db.commit()
        return redirect("/")

    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/content", methods=["POST"])
def content():
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if role.name != "user":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        permissions = role.permissions
        if "create_own_content" not in permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401

        # quote required
        quote = request.form.get("quote", "").strip()
        if not quote:
            return jsonify({"error": "Quote are required.", "status_code": 400}), 400

        # Create new content
        new_content = Content(
            quote=quote,
            status="Active",
            created_by=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(new_content)
        db.commit()
        print("create content successfull")
        return redirect("/")
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/<content_id>", methods=["PATCH"])
def update_content(content_id):
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if role.name != "user":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        permissions = role.permissions
        if "update_own_content" not in permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401
        
        # Query the content by ID
        current_quote = db.query(Content).filter(Content.id == content_id).first()
        if not current_quote:
            return jsonify({"error": "Quote not found", "status_code": 404}), 404

        new_quote = request.form.get("quote", "").strip()
        # If the new quote is empty, fall back to the current quote
        updated_quote = new_quote if new_quote else current_quote.quote
        update_time = datetime.now(timezone.utc) if datetime.now(timezone.utc) else current_quote.created_at

        db.query(Content).filter(Content.id == content_id).update({"quote": updated_quote, "updated_at": update_time})
        db.commit()
        print("update success")
        return redirect("/")
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/<content_id>", methods=["DELETE"])
def delete_content(content_id):
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if role.name != "user":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        permissions = role.permissions
        if "delete_own_content" not in permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401

        db.query(Content).filter(Content.id == content_id).update({"status": "Inactive", "updated_at": datetime.now(timezone.utc)})
        db.commit()
        print("delete content success")
        return redirect("/")
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/ban/<content_id>", methods=["PATCH"])
def ban_content(content_id):
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if role.name != "admin":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        permissions = role.permissions
        if "ban" not in permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401
        
        quote = db.query(Content).filter(Content.id == content_id).first()
        if not quote:
            return jsonify({"error": "Quote not found", "status_code": 404}), 404
        
        if quote.status == "Active":
            db.query(Content).filter(Content.id == content_id).update({"status": "Ban", "updated_at": datetime.now(timezone.utc)})
            db.commit()
            print("ban success")
        elif quote.status == "Ban":
            db.query(Content).filter(Content.id == content_id).update({"status": "Inactive", "updated_at": datetime.now(timezone.utc)})
            db.commit()
            print("unban success")
        return redirect("/")
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/listusers", methods=["GET"])
def list_user():
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        current_role = db.query(Role).filter(Role.id == role_id).first()
        if not current_role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if current_role.name != "superadmin":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        current_permissions = current_role.permissions
        if "updateadmin" not in current_permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401
        
        # check target email
        all_users = db.query(User).all()
        users_list = [{"id": user.id, "email": user.email} for user in all_users]
        print("Users listed successfully")
        return jsonify(users_list)
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

@app.route("/managerole/<target_user_id>", methods=["PATCH"])
def manage_role(target_user_id):
    db: Session = next(get_db())
    try:
        # User must be logged in to create content
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "You must be logged in to create content", "status_code": 401}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User is not found", "status_code": 404}), 404
        
        # role need to be authorized
        role_id = user.role_id
        current_role = db.query(Role).filter(Role.id == role_id).first()
        if not current_role:
            return jsonify({"error": "Role is not found", "status_code": 404}), 404
        if current_role.name != "superadmin":
            return jsonify({"error": "Unauthorized Role", "status_code": 401}), 401
        current_permissions = current_role.permissions
        if "updateadmin" not in current_permissions:
            return jsonify({"error": "Unauthorized Permission", "status_code": 401}), 401
        
        # check user
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return jsonify({"error": "User not found", "status_code": 404}), 404

        # check target role
        target_role_id = target_user.role_id
        target_role = db.query(Role).filter(Role.id == target_role_id).first()
        target_role_name = target_role.name
        if not target_role:
            return jsonify({"error": "Target role is not found", "status_code": 404}), 404
        if target_role.name not in ["user", "admin"]:
            return jsonify({"error": "Target role can not change role", "status_code": 401}), 401
        
        # check new role
        new_role = request.form.get("role", "").strip()
        if new_role not in ["user", "admin"]:
            return jsonify({"error": "Bad request", "status_code": 400}), 400
        new_role = db.query(Role).filter(Role.name == new_role).first()
        new_role_id = new_role.id
        new_role_name = new_role.name
        
        if target_role_name == "user" and new_role_name == "admin":
            db.query(User).filter(User.id == target_user_id).update({"role_id": new_role_id})
            db.commit()
            print("change role from user to admin")
        elif target_role_name == "admin" and new_role_name == "user":
            db.query(User).filter(User.id == target_user_id).update({"role_id": new_role_id})
            db.commit()
            print("change role from admin to user")
        else:
            db.query(User).filter(User.id == target_user_id).update({"role_id": target_role_id})
        
        return redirect("/")
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return jsonify({"error": str(e), "status_code": 500}), 500
    finally:
        db.close()  # Close the session after the operation

if __name__ == "__main__":
    # Get the port from the .env file
    port = int(os.getenv("Port", 5000)) # default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)