import os
from pathlib import Path
from PIL import Image
from src import config

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def validate_image(image_path):
    """
    Validate the saved image file.
    Accepts a Path object or a string path.
    Returns {"valid": bool, "message": str}
    """
    path = Path(image_path)
    
    if not path.exists():
        return {"valid": False, "message": "Image file does not exist."}
        
    if not allowed_file(path.name):
        return {"valid": False, "message": f"Invalid file type. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"}
        
    try:
        # Check size
        size = path.stat().st_size
        if size > config.MAX_CONTENT_LENGTH:
            max_mb = config.MAX_CONTENT_LENGTH / (1024 * 1024)
            return {"valid": False, "message": f"File exceeds maximum size of {max_mb:.1f}MB."}
    except Exception as e:
        return {"valid": False, "message": f"Failed to check file size: {str(e)}"}
        
    try:
        # Verify image integrity using PIL
        with Image.open(path) as img:
            img.verify()
    except Exception:
        return {"valid": False, "message": "Uploaded file is corrupted or not a valid image."}
        
    return {"valid": True, "message": ""}
