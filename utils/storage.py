"""
utils/storage.py - Unified File Storage Adapter
Supports both private Supabase Object Storage (for persistent cloud deployment on Render)
and local filesystem storage (for local development and offline testing).
"""
import os
import requests
from flask import current_app


CATEGORY_FOLDER_KEYS = {
    'project_files': 'PROJECT_FILE_FOLDER',
    'resumes': 'RESUME_FOLDER',
    'profile_images': 'PROFILE_IMAGE_FOLDER',
    'certificates': 'CERTIFICATE_FOLDER',
    'reports': 'UPLOAD_FOLDER',
}


def is_cloud_storage_enabled():
    """Returns True if Supabase Storage credentials are configured."""
    supabase_url = current_app.config.get('SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    supabase_key = current_app.config.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')
    return bool(supabase_url and supabase_key)


def _get_cloud_config():
    supabase_url = (current_app.config.get('SUPABASE_URL') or os.environ.get('SUPABASE_URL') or '').rstrip('/')
    supabase_key = current_app.config.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY') or ''
    bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET') or os.environ.get('SUPABASE_STORAGE_BUCKET', 'projecthub-uploads')
    return supabase_url, supabase_key, bucket


def save_file(file_obj_or_bytes, category: str, filename: str) -> str:
    """
    Saves a file to persistent storage (Supabase in cloud, or local filesystem in dev).
    :param file_obj_or_bytes: A FileStorage object, bytes, or file-like object.
    :param category: One of 'project_files', 'resumes', 'profile_images', 'certificates', 'reports'.
    :param filename: Clean, sanitized filename.
    :return: Sanitized filename string.
    """
    # 1. Read bytes
    if hasattr(file_obj_or_bytes, 'read'):
        content = file_obj_or_bytes.read()
        if hasattr(file_obj_or_bytes, 'seek'):
            file_obj_or_bytes.seek(0)
    elif isinstance(file_obj_or_bytes, bytes):
        content = file_obj_or_bytes
    else:
        raise ValueError("Invalid file content type.")

    # 2. Always persist to local cache/directory for local dev and fast fallback
    folder_key = CATEGORY_FOLDER_KEYS.get(category, 'UPLOAD_FOLDER')
    target_dir = current_app.config.get(folder_key) or os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), category)
    os.makedirs(target_dir, exist_ok=True)
    local_path = os.path.join(target_dir, filename)
    with open(local_path, 'wb') as f:
        f.write(content)

    # 3. If cloud storage is enabled, upload to private Supabase bucket
    if is_cloud_storage_enabled():
        supabase_url, supabase_key, bucket = _get_cloud_config()
        cloud_path = f"{category}/{filename}"
        url = f"{supabase_url}/storage/v1/object/{bucket}/{cloud_path}"
        headers = {
            'Authorization': f'Bearer {supabase_key}',
            'apiKey': supabase_key,
            'x-upsert': 'true',
        }
        try:
            resp = requests.post(url, headers=headers, data=content, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"Failed to upload {filename} to Supabase Storage: {e}")
            # If in production and cloud fails, raise to prevent silent loss
            if not current_app.config.get('TESTING'):
                raise

    return filename


def get_file_bytes(category: str, filename: str) -> bytes:
    """
    Retrieves file content bytes from storage (local disk first, then Supabase if cloud enabled).
    :param category: Storage category name.
    :param filename: The filename.
    :return: File bytes or None if not found.
    """
    # Check local disk first
    folder_key = CATEGORY_FOLDER_KEYS.get(category, 'UPLOAD_FOLDER')
    target_dir = current_app.config.get(folder_key) or os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), category)
    local_path = os.path.join(target_dir, filename)
    if os.path.exists(local_path):
        with open(local_path, 'rb') as f:
            return f.read()

    # If missing locally and cloud storage is enabled, fetch from Supabase
    if is_cloud_storage_enabled():
        supabase_url, supabase_key, bucket = _get_cloud_config()
        cloud_path = f"{category}/{filename}"
        url = f"{supabase_url}/storage/v1/object/authenticated/{bucket}/{cloud_path}"
        headers = {
            'Authorization': f'Bearer {supabase_key}',
            'apiKey': supabase_key,
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                # Cache locally for subsequent requests
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    with open(local_path, 'wb') as f:
                        f.write(resp.content)
                except Exception:
                    pass
                return resp.content
        except Exception as e:
            current_app.logger.error(f"Failed to fetch {filename} from Supabase Storage: {e}")

    return None
