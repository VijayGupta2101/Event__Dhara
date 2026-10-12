import os
import re
import io
import base64
import hashlib
from pathlib import Path
from PIL import Image

def compute_md5(data: bytes | str | Path) -> str:
    """Computes MD5 hash from raw bytes or a file path."""
    hasher = hashlib.md5()
    if isinstance(data, (str, Path)):
        with open(data, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
    elif isinstance(data, bytes):
        hasher.update(data)
    else:
        raise ValueError("Data must be bytes or a file path")
    return hasher.hexdigest()

def sanitize_filename(name: str, max_length: int = 40) -> str:
    """Sanitizes a string to be a safe Windows/Linux filename."""
    if not name:
        return "event_image"
    # Remove illegal filename characters
    clean = re.sub(r'[\\/*?:"<>|#&%$\'\"]', "", name)
    clean = re.sub(r'[\s\-]+', "_", clean).strip("_").lower()
    if not clean:
        clean = "event_image"
    return clean[:max_length]

def format_image_id(serial_number: int) -> str:
    """Generates standardized EventDhara Image ID e.g. ED-IMG-0001."""
    return f"ED-IMG-{serial_number:04d}"

def resize_and_encode_image(image_path: str | Path, max_dimension: int = 1600) -> tuple[str, str]:
    """
    Loads an image, optionally resizes it if it exceeds max_dimension,
    and returns its base64 string and MIME type for Vision API consumption.
    """
    image_path = Path(image_path)
    with Image.open(image_path) as img:
        # Determine MIME type
        format_str = (img.format or "JPEG").upper()
        if format_str in ["JPEG", "JPG"]:
            mime_type = "image/jpeg"
        elif format_str == "PNG":
            mime_type = "image/png"
        elif format_str == "WEBP":
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"

        # Check if resize is needed
        width, height = img.size
        if max(width, height) > max_dimension:
            scale = max_dimension / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Convert RGBA to RGB if saving to JPEG
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if resized.mode in ("RGBA", "P") and mime_type == "image/jpeg":
                resized = resized.convert("RGB")
                
            buffer = io.BytesIO()
            save_format = "PNG" if mime_type == "image/png" else "JPEG"
            resized.save(buffer, format=save_format, quality=90)
            img_bytes = buffer.getvalue()
        else:
            with open(image_path, "rb") as f:
                img_bytes = f.read()

        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        return base64_str, mime_type

def save_env_key(key: str, value: str, env_file_path: Path | str) -> bool:
    """Updates or adds an environment variable in the .env file."""
    env_path = Path(env_file_path)
    lines = []
    found = False
    
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_lines.append(f"{key}={value}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    return True

def format_file_size(num_bytes: int) -> str:
    """Formats bytes into human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"
