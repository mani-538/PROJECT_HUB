"""
config.py - Application Configuration
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'project-hub-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'project_hub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folders
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PROFILE_IMAGE_FOLDER = os.path.join(BASE_DIR, 'uploads', 'profile_images')
    RESUME_FOLDER = os.path.join(BASE_DIR, 'uploads', 'resumes')
    PROJECT_FILE_FOLDER = os.path.join(BASE_DIR, 'uploads', 'project_files')
    CERTIFICATE_FOLDER = os.path.join(BASE_DIR, 'uploads', 'certificates')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
    ALLOWED_PROJECT_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip', 'rar', 'py', 'ipynb', 'txt', 'png', 'jpg', 'mp4'}
