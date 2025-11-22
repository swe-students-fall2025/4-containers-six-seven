"""
File handling utilities for receipt uploads.

This module:
- Validates allowed file extensions
- Generates unique filenames
- Saves uploaded files into the UPLOAD_FOLDER
"""

import os
import uuid
from werkzeug.utils import secure_filename

# Allowed image types
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Folder to store uploads - use absolute path relative to project root
# This ensures worker can find files regardless of where it runs from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")


def allowed_file(filename: str) -> bool:
    """
    Check if the uploaded filename has a valid image extension.

    Example:
        allowed_file("receipt.jpg") -> True
        allowed_file("script.exe") -> False
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file) -> str:
    """
    Save an uploaded file to the uploads folder with a unique filename.

    Args:
        file: Werkzeug FileStorage object

    Returns:
        str: Absolute or relative path of the saved file

    Notes:
        - The uploads folder is created if it does not exist.
        - Filenames are randomized to avoid collisions.
    """
    # Generate safe and unique filename
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()

    new_name = f"{uuid.uuid4().hex}.{ext}"

    # Ensure upload folder exists (create if it doesn't)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Use absolute path to ensure file is saved in the correct location
    save_path = os.path.join(UPLOAD_FOLDER, new_name)
    save_path = os.path.abspath(os.path.normpath(save_path))

    print(f"[DEBUG] Saving file to: {save_path}")
    print(f"[DEBUG] UPLOAD_FOLDER: {UPLOAD_FOLDER}")
    print(f"[DEBUG] Folder exists: {os.path.exists(UPLOAD_FOLDER)}")

    # Save file bytes using absolute path
    file.save(save_path)

    # Verify file was saved
    if not os.path.exists(save_path):
        raise IOError(f"Failed to save file to {save_path}")

    print(f"[DEBUG] File saved successfully: {save_path}")
    print(f"[DEBUG] File exists: {os.path.exists(save_path)}")

    return save_path
