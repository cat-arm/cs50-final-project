# LoveQuotes
#### Video Demo: https://www.youtube.com/watch?v=lZnvP881KfE
#### Description:
LoveQuotes is a web-based application designed to connect users through meaningful quotes. With a focus on simplicity and community engagement, this project enables users to share their best thoughts, manage content, and interact with a structured user role system. The goal is to create an intuitive platform that combines creativity with robust user and content management functionality.

The application showcases a seamless integration of Python, Flask, and modern tools like Tailwind CSS for a polished user experience. It also leverages Supabase for database management, ensuring reliability and scalability

## Features:
**User Management**
- Enables users to register and securely log in to the platform.
- Implements secure password hashing using passlib with Argon2.
- Session management using Flask-Session to provide secure and persistent user sessions.
**Role Management**
- Users can be assigned specific roles: Public, User, Admin, or Superadmin.
- Superadmins can manage user roles, promoting or demoting users between User and Admin.
**Content Management**
- Registered users can create, edit, and delete their quotes.
- Public users can browse quotes but cannot modify or interact with them.
**Special Features for Admins**
- Admins have the ability to ban content that violates community guidelines.
- Superadmins oversee overall platform management and enforce stricter controls.
**Scalability and Responsiveness**
- Built with Flask and Tailwind CSS for a responsive and mobile-friendly user experience.
- Supabase ensures efficient data storage and retrieval.

## Roles
**Public**
- Read-only access to all quotes.
**User**
- Can register, log in, and manage their quotes (create, edit, and delete).
**Admin**
- All User privileges.
- Can ban inappropriate content.
**Superadmin**
- All Admin privileges.
- Can promote or demote users between User and Admin roles

## Tech Stack
**Backend**
- Python
- Flask (web framework)
- Flask-SQLAlchemy (ORM)
- Flask-Limiter (rate limiting for security)
**Frontend**
- HTML and CSS
- Tailwind CSS for modern, responsive design
**Database**
- Supabase: A cloud-based database solution with easy integration for Flask.

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

## Requirements
- Python 3.x
- pip (Python package installer)

## Steps to Install
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

7. **Install Tailwind CSS Dependencies**

   ```bash
   npm install
   ```

8. **Build Tailwind CSS**

   ```bash
   npm run build
   ```

9. **Create a .env File**
Add the following environment variable
   ```bash
   SUPABASE_URL=youe-database-url
   SUPABASE_KEY=your-database-key
   PORT=your-port
   SUPERADMIN_EMAIL="your-email"
   SUPERADMIN_PASSWORD="your-password"
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   ```

10. **Initialize the Database**

   ```bash
   python database. py
   ```

11. **Run the application**

   ```bash
   flask run --reload
   ```

12. **Access the Application**

   ```bash
    http://localhost:5000
   ```
