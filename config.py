"""
config.py - Application Configuration
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Safely load local .env if present
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

def _get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if not key:
        raise RuntimeError(
            "SECRET_KEY is required. Please set the SECRET_KEY environment variable "
            "or configure it in your .env file."
        )
    return key

class Config:
    SECRET_KEY = _get_secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('sqlite:///' + os.path.join(BASE_DIR, 'project_hub.db'))
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DISABLE_DESTRUCTIVE_ADMIN = os.environ.get('DISABLE_DESTRUCTIVE_ADMIN', 'true').lower() in ('true', '1', 'yes')

    # Cloud Storage (Supabase Storage for persistent deployment on Render)
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')
    SUPABASE_STORAGE_BUCKET = os.environ.get('SUPABASE_STORAGE_BUCKET', 'projecthub-uploads')

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
