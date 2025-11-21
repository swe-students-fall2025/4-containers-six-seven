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

# Folder to store uploads (relative to project root)
UPLOAD_FOLDER = "uploads"


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
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    save_path = os.path.join(UPLOAD_FOLDER, new_name)

    # Save file bytes
    file.save(save_path)

    return save_path