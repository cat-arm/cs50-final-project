import os
from datetime import timedelta, datetime, timezone
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
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
    return render_template("index.html", contents=contents)

@app.route("/session", methods=["GET"])
def check_session():
    user_id = session.get("user_id")
    if user_id:
        return jsonify({"message": f"User is logged in with ID {user_id}"})
    return jsonify({"message": "No user is logged in"}), 401

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get data from the form    
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

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
            return redirect(url_for("index"))
        
        return render_template("login.html", error="Invalid credentials.")
    
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    # Clear session data
    session.clear()
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get data from the form
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        bio = request.form.get("bio", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        password_confirm= request.form.get("password_confirm", "").strip()

        # Check valid pasword
        if not is_valid_password(password):
            return render_template("register.html", error="Invalid password format.")
    
        # Check password and confirmation password match
        if not password == password_confirm:
            return render_template("register.html", error="Passwords do not match.")

        # Check required field
        if not all([first_name, last_name, email, password]):
            return render_template("register.html", error="All fields are required.")

        # check valid email
        valid_email = is_valid_email(email)
        if not valid_email:
            return render_template("register.html", error="Invalid email address.")
    
        #hash password
        password_hash = hash_password(password)

        # Get the database session
        db: DBSession = next(get_db())

        try:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return render_template("register.html", error="Email already registered.")
        
            # Get the role object where name is user
            role = db.query(Role).filter(Role.name == "user").first()
            # Check if the role exists
            if not role:
                return render_template("error.html", message="Role not found.")

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
            return redirect(url_for("login"))

        except Exception as e:
            db.rollback()  # Rollback on error
            return render_template("error.html", message=f"Error: {str(e)}")
        finally:
            db.close()  # Close the session after the operation
    return render_template("register.html")

@app.route("/content", methods=["POST"])
def content():
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    # quote required
    quote = request.form.get("quote", "").strip()
    if not quote:
        return render_template("index.html", error="Quote is required.")
    
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "user" or "create_own_content" not in role.permissions:
            return render_template("index.html", error="Unauthorized to create content.")

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
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/<content_id>", methods=["PATCH"])
def update_content(content_id):
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    # quote required
    new_quote = request.form.get("quote", "").strip()
    if not new_quote:
        return render_template("index.html", error="Quote is required.")
    
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "user" or "update_own_content" not in role.permissions:
            return render_template("index.html", error="Unauthorized to update content.")
        
        # Query the content by ID
        current_quote = db.query(Content).filter(Content.id == content_id).first()
        if not current_quote:
            render_template("error.html", message="Quote not found.")

        # If the new quote is empty, fall back to the current quote
        updated_quote = new_quote if new_quote else current_quote.quote
        update_time = datetime.now(timezone.utc) if datetime.now(timezone.utc) else current_quote.created_at

        db.query(Content).filter(Content.id == content_id).update({"quote": updated_quote, "updated_at": update_time})
        db.commit()
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/<content_id>", methods=["DELETE"])
def delete_content(content_id):
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "user" or "delete_own_content" not in role.permissions:
            return render_template("index.html", error="Unauthorized to delete content.")

        db.query(Content).filter(Content.id == content_id).update({"status": "Inactive", "updated_at": datetime.now(timezone.utc)})
        db.commit()
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/ban/<content_id>", methods=["PATCH"])
def ban_content(content_id):
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "admin" or "ban" not in role.permissions:
            return render_template("index.html", error="Unauthorized to ban content.")
        
        quote = db.query(Content).filter(Content.id == content_id).first()
        if not quote:
            return render_template("error.html", message="Quote not found.")
        
        if quote.status == "Active":
            db.query(Content).filter(Content.id == content_id).update({"status": "Ban", "updated_at": datetime.now(timezone.utc)})
            db.commit()
        elif quote.status == "Ban":
            db.query(Content).filter(Content.id == content_id).update({"status": "Inactive", "updated_at": datetime.now(timezone.utc)})
            db.commit()
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/listusers", methods=["GET"])
def list_user():
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
            
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "superadmin" or "updateadmin" not in role.permissions:
            return render_template("index.html", error="Unauthorized to list users.")
        
        # check target email
        all_users = db.query(User).all()
        users_list = [{"id": user.id, "email": user.email} for user in all_users]
        return jsonify(users_list)
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/managerole/<target_user_id>", methods=["PATCH"])
def manage_role(target_user_id):
    # User must be logged in to create content
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    new_role = request.form.get("role", "").strip()
    if new_role not in ["user", "admin"]:
        return render_template("error.html", message="Bad Request.")
    
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return render_template("error.html", message="User not found.")
        
        # role need to be authorized
        role_id = user.role_id
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name != "superadmin" or "updateadmin" not in role.permissions:
            return render_template("index.html", error="Unauthorized to list users.")
        
        # check user
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return render_template("error.html", message="Target user not found.")

        # check target role
        target_role_id = target_user.role_id
        target_role = db.query(Role).filter(Role.id == role_id).first()
        if not target_role or target_role.name not in ["user", "admin"]:
            return render_template("index.html", error="Failed to give admin authority.")
        
        # check new role
        new_role = db.query(Role).filter(Role.name == new_role).first()
        new_role_id = new_role.id
        new_role_name = new_role.name
        
        if target_role.name  == "user" and new_role_name == "admin":
            db.query(User).filter(User.id == target_user_id).update({"role_id": new_role_id})
            db.commit()
        elif target_role.name  == "admin" and new_role_name == "user":
            db.query(User).filter(User.id == target_user_id).update({"role_id": new_role_id})
            db.commit()
        else:
            db.query(User).filter(User.id == target_user_id).update({"role_id": target_role_id})
            db.commit()
        
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return render_template("error.html", message=f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

if __name__ == "__main__":
    # Get the port from the .env file
    port = int(os.getenv("Port", 5000)) # default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)