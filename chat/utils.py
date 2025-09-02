from PIL import Image
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import uuid


def compress_image(image_file, max_size=(800, 600), quality=85):
    """Compress image for chat sharing"""
    try:
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save compressed image
        from io import BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Generate new filename
        filename = f"chat_media/{uuid.uuid4().hex}.jpg"
        
        return default_storage.save(filename, ContentFile(output.read()))
    except Exception:
        return None


def get_file_size_mb(file):
    """Get file size in MB"""
    return file.size / (1024 * 1024)


def is_allowed_file_type(filename):
    """Check if file type is allowed"""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)
