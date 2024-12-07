# LoveQuotes

### Video Demo: https://www.youtube.com/watch?v=lZnvP881KfE

## Description

Share your best code for each other.

## Features

- **User Management**: Allows users to register, login.
- **Role Management**: Users can be assigned different roles --> admin, user.
- **Content Management**: Users can create, edit, and delete their own content.
- **Special Management**: Admins can ban content.

## Roles

- **Public**: Allows to read all qoutes
- **User**: Allows users to register, login, create qoute, update qoute, delete qoute.
- **Admin**: Allows to ban content.
- **Superadmin**: Allows to select some account to switch role between user and admin.

## Tech Stack

- **Python**: Programming language used.
- **Flask**: Web framework.
- **SQLAlchemy**: ORM for interacting with the database.
- **HTML/CSS**: Frontend styling.
- **tailwind**: CSS framework
- **Supabase**: Database hosting.

## Installation

- Flask
- Flask-Session
- Flask-SQLAlchemy
- Flask-Limiter
- Flask-Migrate
- supabase
- python-dotenv
- psycopg2-binary
- passlib[argon2]

### Requirements

- Python 3.x
- pip (Python package installer)

### Steps to Install

1. **Clone the repository**

   ```bash
   git clone https://github.com/paiigak/cs50-final-project.git
   ```

2. **Navigate to the project directory**

   ```bash
   cd cs50-final-project
   ```

3. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment

   **On Windows**

   ```bash
   .\venv\Scripts\Activate
   ```

   **On macOS/Linux**

   ```bash
   source venv/bin/activate
   ```

5. **deactivate the virtual environment**

   ```bash
   deactivate
   ```

6. **Install the required dependencies**

   ```bash
   pip install -r requirements.txt
   ```

7. **Create file .env to set environment and register database or supabase**

   ```bash
   SUPABASE_URL=youe-database-url
   SUPABASE_KEY=your-databse-key
   PORT=your-port

   SUPERADMIN_EMAIL="your-enail"
   SUPERADMIN_PASSWORD="your-password"

   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   ```

8. **Set superadmin account and create model at supabase**

   ```bash
   database. py
   ```

9. **Run the application**

   ```bash
   flask run --reload
   ```
