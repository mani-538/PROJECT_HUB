# Project Hub – Academic Project Management System

Project Hub is an AI-powered student project management platform designed to streamline collaboration, tracking, and certification of academic projects.

## 🚀 Key Features
- **Admin Dashboard**: Comprehensive management of students, projects, and queries.
- **Student Portal**: Project submission, real-time status tracking, and AI-powered suggestions.
- **AI Integration**: Automatic project descriptions and resume analysis.
- **Certification System**: Automated generation and verification of project completion certificates.
- **System Reports**: Real-time PDF reporting for administrative oversight.

## 🛠️ Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript (Glassmorphism & SaaS branding)
- **PDF Generation**: ReportLab
- **Authentication**: Flask-Login

## 📦 Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/PROJECT_HUB.git
   cd PROJECT_HUB
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   Access the app at `http://127.0.0.1:5000`.

## 🌐 Deployment Logic
To deploy this application to a live server:
1. Push this code to a **GitHub** repository.
2. Connect the repository to a hosting provider like **Render**, **Railway**, or **PythonAnywhere**.
3. Use `app:create_app()` as the entry point and `gunicorn` as the WSGI server.
