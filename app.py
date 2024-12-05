import os
from datetime import timedelta, datetime, timezone
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql import func
from dotenv import load_dotenv
from models import Role, User, Content
from utils import get_db, is_valid_password, is_valid_email, hash_password, check_password, get_current_user, check_permission, handle_error


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mysecretkey")  # Secret key for sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_PERMANENT'] = True # Session should last even after browser is closed
Session(app)  # Initialize session management

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

@app.route("/", methods=["GET"])
def index():
    db: Session = next(get_db())
    contents = (
        db.query(
            Content.id,
            Content.quote,
            Content.status,
            Content.created_by,
            Content.created_at,
            func.concat(User.first_name, " ", User.last_name).label("posts_by")
        )
        .join(User, Content.created_by == User.id)  # Join Content with User based on created_by
        .filter(Content.status != "Inactive")  # Exclude inactive content
        .order_by(Content.created_at.desc())
        .all()
    )
    contents_list = [{"id": content.id, "quote": content.quote, "status": content.status, "created_by": content.created_by, "posts_by": content.posts_by} for content in contents]
    users = db.query(User).all()
    db.close()
    print(contents_list)
    return render_template("index.html", contents=contents_list, users=users)

@app.route("/session", methods=["GET"])
def check_session():
    user = get_current_user()
    if user:
        return jsonify({"message": f"User is logged in with ID {user.id}"})
    return jsonify({"message": "No user is logged in"}), 401

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        # Get data from the form    
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        # Check if the email exists in the database
        db: DBSession = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        # If the user is found and password matches
        if user and check_password(password, user.password_hash):
            session.permanent = True
            # Store user ID in session
            session["user_id"] = user.id
            session["role"] = user.role.name
            session["permissions"] = user.role.permissions
            print(session["permissions"])

            # Set session expiry (30 days)
            app.permanent_session_lifetime = timedelta(days=30)
            print("Login successful")
            return redirect(url_for("index"))

        # If email or password does not match
        return render_template("login.html", error="Your email or password did not match.")

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    # Clear session data
    session.clear()
    print("logout successful")
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
        password_confirm = request.form.get("password_confirm", "").strip()

        # Validation
        if not is_valid_password(password):
            return render_template(
                "register.html",
                error="Invalid password. Password must be at least 8 characters, with 1 uppercase and 1 symbol.",
                data=request.form,
            )

        if password != password_confirm:
            return render_template(
                "register.html",
                error="Password and Confirm Password do not match.",
                data=request.form,
            )

        if not all([first_name, last_name, email, password]):
            return render_template(
                "register.html",
                error="All fields are required.",
                data=request.form,
            )

        if not is_valid_email(email):
            return render_template(
                "register.html",
                error="Invalid email address.",
                data=request.form,
            )

        # Hash password
        password_hash = hash_password(password)

        db: DBSession = next(get_db())

        try:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return render_template(
                    "register.html",
                    error="Email already registered.",
                    data=request.form,
                )

            role = db.query(Role).filter(Role.name == "user").first()
            if not role:
                return render_template("error.html", message="Role not found.")

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                bio=bio,
                email=email,
                password_hash=password_hash,
                role_id=role.id,
            )
            db.add(new_user)
            db.commit()

            session.permanent = True
            session["user_id"] = new_user.id
            app.permanent_session_lifetime = timedelta(days=30)
            return redirect(url_for("index"))

        except Exception as e:
            db.rollback()
            return handle_error(f"Error: {str(e)}")
        finally:
            db.close()

    # Handle GET request
    return render_template("register.html", data={})

@app.route("/createquote", methods=["GET", "POST"])
def create_content():
    # User must be logged in to create content
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    if not check_permission(user, "create_own_content"):
        return handle_error("Unauthorized to create content.")
    
    if request.method == "POST":
        # Quote required
        quote = request.form.get("quote", "").strip()
        if not quote:
            return render_template("index.html", error="Quote is required.")
    
        db: Session = next(get_db())
    
        try:
            # Create new content
            new_content = Content(
                quote=quote,
                status="Active",
                created_by=user.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.add(new_content)
            db.commit()
            print("Content created successfully")
            return redirect(url_for("index"))
            
        except Exception as e:
            db.rollback()  # Rollback on error
            return handle_error(f"Error: {str(e)}")
        finally:
            db.close()  # Close the session after the operation

    # If the method is GET
    return render_template("createquote.html")

@app.route("/content/<content_id>/edit", methods=["GET", "POST"])
def update_content(content_id):
    # User must be logged in to update content
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    db: Session = next(get_db())

    if not check_permission(user, "update_own_content"):
        return handle_error("Unauthorized to update content.")

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return handle_error("Content not found.")

    # Check if the user is authorized to update this content
    if content.created_by != user.id:
        return handle_error("You do not have permission to edit this content.")
        
    if content.status == "Inactive":
        return handle_error("This Quote is inactive.")

    if request.method == "POST":
        try:
            # Get the new quote from the form; if not provided, use the current quote
            new_quote = request.form.get("quote", "").strip()
            if content.status == "Ban":
                content.status = "Active"
                content.updated_at = datetime.now(timezone.utc)
                if not new_quote:
                    return render_template("index.html", error="New quote is required.")
            else:
                content.quote = new_quote if new_quote else content.quote
                content.updated_at = datetime.now(timezone.utc)

            db.commit()
            print("Content update successful")
            return redirect(url_for("index"))
        except Exception as e:
            db.rollback()  # Rollback on error
            return handle_error(f"Error: {str(e)}")
        finally:
            db.close()  # Close the session after the operation
    
    # If the method is GET, render the update form
    return render_template("updatequote.html", content=content)

@app.route("/content/<content_id>/delete", methods=["GET"])
def delete_content(content_id):
    # User must be logged in to create content
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    db: Session = next(get_db())
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            return handle_error("Content not found.")
        
        # Check if the user is authorized to delete this content
        if content.created_by != user.id:
            return handle_error("You do not have permission to delete this content.")
        
        if content.status == "Inactive":
            return handle_error("This Quote was not found.")
        
        content.status = "Inactive"
        content.updated_at = datetime.now(timezone.utc)

        db.commit()
        print("delete content successful")
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return handle_error(f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/content/<content_id>/ban", methods=["GET"])
def ban_content(content_id):
    # User must be logged in to create content
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if not check_permission(user, "ban"):
        return handle_error("Unauthorized to ban content.")
    
    db: Session = next(get_db())
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            return handle_error("Content not found.")
        
        # Check if the content is already inactive
        if content.status == "Inactive" or content.status == "Ban":
            return handle_error("This content is already archived or baded and cannot be banned.")
        
        content.status = "Ban" if content.status == "Active" else "Inactive"
        content.updated_at = datetime.now(timezone.utc)

        db.commit()
        print("ban content successful")
        return redirect(url_for("index"))
            
    except Exception as e:
        db.rollback()  # Rollback on error
        return handle_error(f"Error: {str(e)}")
    finally:
        db.close()  # Close the session after the operation

@app.route("/managerole", methods=["GET", "POST"])
def managerole():
    # Ensure user is logged in
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if not check_permission(user, "updateadmin"):
        return handle_error("Unauthorized to change user role.")

    db: Session = next(get_db())

    if request.method == "POST":
        # Handle the role update logic here
        target_user_id = request.form.get("user_id")
        new_role = request.form.get("role", "").strip()

        # Proceed with role update (same as before)
        if new_role not in ["user", "admin"]:
            return handle_error("Invalid role.")

        try:
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if not target_user:
                return handle_error("User not found.")

            role = db.query(Role).filter(Role.name == new_role).first()
            if not role:
                return handle_error("Role not found.")

            target_user.role_id = role.id
            db.commit()
            return redirect(url_for("index"))

        except Exception as e:
            db.rollback()
            return handle_error(f"Error: {str(e)}")

    # GET request: fetch users for role management
    users = db.query(User).filter(User.id != user.id).join(Role).filter(Role.name != 'superadmin').all()

    db.close()
    return render_template("managerole.html", users=users)

if __name__ == "__main__":
    # Get the port from the .env file
    port = int(os.getenv("Port", 5000)) # default to 5000 if PORT is not set
    app.run(debug=True, host="0.0.0.0", port=port)