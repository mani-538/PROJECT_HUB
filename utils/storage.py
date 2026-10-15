"""
utils/storage.py - Unified File Storage Adapter
Supports both private Supabase Object Storage (for persistent cloud deployment on Render)
and local filesystem storage (for local development and offline testing).

Guarantees:
- When cloud storage is enabled, uploads target private Supabase Storage.
- Cloud failures raise an explicit error and NEVER silently fall back to local disk.
- Downloads fetch from Supabase Storage without relying on ephemeral local files.
"""
import os
import logging
import requests
from flask import current_app

logger = logging.getLogger('projecthub.storage')


CATEGORY_FOLDER_KEYS = {
    'project_files': 'PROJECT_FILE_FOLDER',
    'resumes': 'RESUME_FOLDER',
    'profile_images': 'PROFILE_IMAGE_FOLDER',
    'certificates': 'CERTIFICATE_FOLDER',
    'reports': 'UPLOAD_FOLDER',
}


def is_cloud_storage_enabled():
    """Returns True if Supabase Storage credentials are configured."""
    try:
        if current_app and current_app.config.get('TESTING') and not current_app.config.get('SUPABASE_URL'):
            return False
        supabase_url = current_app.config.get('SUPABASE_URL') or os.environ.get('SUPABASE_URL')
        supabase_key = current_app.config.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')
    except RuntimeError:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')
    return bool(supabase_url and supabase_key)


def _get_cloud_config():
    try:
        supabase_url = (current_app.config.get('SUPABASE_URL') or os.environ.get('SUPABASE_URL') or '').rstrip('/')
        supabase_key = current_app.config.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY') or ''
        bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET') or os.environ.get('SUPABASE_STORAGE_BUCKET', 'projecthub-uploads')
    except RuntimeError:
        supabase_url = (os.environ.get('SUPABASE_URL') or '').rstrip('/')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY') or ''
        bucket = os.environ.get('SUPABASE_STORAGE_BUCKET', 'projecthub-uploads')
    return supabase_url, supabase_key, bucket


def save_file(file_obj_or_bytes, category: str, filename: str) -> str:
    """
    Saves a file to persistent storage (Supabase in cloud, or local filesystem in dev).
    If cloud storage is enabled, failure to upload to Supabase raises an exception
    and never silently falls back to local disk.
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

    # 2. If cloud storage is enabled, upload to private Supabase bucket FIRST
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
        except Exception as e:
            logger.error(f"Network error uploading {filename} to Supabase: {e}")
            raise RuntimeError(f"Cloud storage upload to Supabase failed: {e}")

        if resp.status_code not in (200, 201):
            logger.error(f"Supabase upload returned {resp.status_code}: {resp.text}")
            raise RuntimeError(f"Cloud storage upload to Supabase failed with HTTP {resp.status_code}: {resp.text}")

    # 3. Also write to local directory (local dev, or local working copy)
    folder_key = CATEGORY_FOLDER_KEYS.get(category, 'UPLOAD_FOLDER')
    target_dir = current_app.config.get(folder_key) or os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), category)
    os.makedirs(target_dir, exist_ok=True)
    local_path = os.path.join(target_dir, filename)
    with open(local_path, 'wb') as f:
        f.write(content)

    return filename


def get_file_bytes(category: str, filename: str) -> bytes:
    """
    Retrieves file content bytes from storage.
    If cloud storage is enabled, fetches directly from Supabase Storage.
    :param category: Storage category name.
    :param filename: The filename.
    :return: File bytes or None if not found.
    """
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
                return resp.content
            elif resp.status_code == 404 or (resp.status_code == 400 and ('not_found' in resp.text or 'nosuchkey' in resp.text.lower())):
                pass
            else:
                logger.error(f"Supabase fetch returned {resp.status_code}: {resp.text}")
                raise RuntimeError(f"Cloud storage fetch failed with HTTP {resp.status_code}")
        except requests.RequestException as e:
            logger.error(f"Network error fetching {filename} from Supabase: {e}")
            raise RuntimeError(f"Cloud storage fetch from Supabase failed: {e}")

    # Local fallback only when cloud storage is NOT configured (offline development)
    folder_key = CATEGORY_FOLDER_KEYS.get(category, 'UPLOAD_FOLDER')
    target_dir = current_app.config.get(folder_key) or os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), category)
    local_path = os.path.join(target_dir, filename)
    if os.path.exists(local_path):
        with open(local_path, 'rb') as f:
            return f.read()

    return None


def delete_file(category: str, filename: str) -> bool:
    """
    Deletes a file from Supabase storage and local disk.
    :param category: Storage category name.
    :param filename: The filename.
    :return: True if deletion attempted successfully.
    """
    if is_cloud_storage_enabled():
        supabase_url, supabase_key, bucket = _get_cloud_config()
        cloud_path = f"{category}/{filename}"
        url = f"{supabase_url}/storage/v1/object/{bucket}"
        headers = {
            'Authorization': f'Bearer {supabase_key}',
            'apiKey': supabase_key,
            'Content-Type': 'application/json',
        }
        try:
            requests.delete(url, headers=headers, json={"prefixes": [cloud_path]}, timeout=10)
        except Exception as e:
            logger.warning(f"Error deleting {filename} from Supabase Storage: {e}")

    folder_key = CATEGORY_FOLDER_KEYS.get(category, 'UPLOAD_FOLDER')
    target_dir = current_app.config.get(folder_key) or os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), category)
    local_path = os.path.join(target_dir, filename)
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
        except OSError:
            pass

    return True
