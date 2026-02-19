"""
Utility functions for Fleet-Management.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from werkzeug.utils import secure_filename

# =============================================================================
# Timezone Utilities
# =============================================================================

def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_local_time(dt: datetime, tz: Optional[timezone] = None) -> datetime:
    """Convert UTC datetime to local timezone."""
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    
    if tz is None:
        # Default to PKT (Pakistan Standard Time)
        from datetime import timedelta
        tz = timezone(timedelta(hours=5))
    
    return dt.astimezone(tz)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime for display."""
    if dt.tzinfo:
        dt = to_local_time(dt)
    return dt.strftime(format_str)


# =============================================================================
# File Upload Utilities
# =============================================================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_upload_filename(entity_type: str, entity_id: int, original_filename: str) -> str:
    """Generate a safe, unique filename for upload."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    safe_name = f"{entity_type}_{entity_id}_{uuid.uuid4().hex}.{ext}"
    return secure_filename(safe_name)


def ensure_upload_folder():
    """Create upload folder if it doesn't exist."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_upload(file, entity_type: str, entity_id: int) -> str:
    """
    Save an uploaded file and return the relative path.
    
    Args:
        file: FileStorage object from request.files
        entity_type: Type of entity (e.g., 'incident', 'fuel_entry')
        entity_id: ID of the entity
        
    Returns:
        Relative path to saved file (e.g., 'uploads/incident_123_abc123.pdf')
        
    Raises:
        ValueError: If file is not allowed
    """
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}")
    
    ensure_upload_folder()
    
    safe_filename = generate_upload_filename(entity_type, entity_id, file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
    
    file.save(filepath)
    
    return f"uploads/{safe_filename}"


# =============================================================================
# Validation Utilities
# =============================================================================

def validate_positive(value, field_name: str):
    """Validate that a value is positive."""
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def validate_not_negative(value, field_name: str):
    """Validate that a value is not negative."""
    if value is not None and value < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return value


def sanitize_string(value: Optional[str], max_length: int = 255) -> Optional[str]:
    """Sanitize a string value."""
    if value is None:
        return None
    
    value = value.strip()
    if not value:
        return None
    
    return value[:max_length]


# =============================================================================
# Number Utilities
# =============================================================================

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default on division by zero."""
    if denominator is None or denominator == 0:
        return default
    return numerator / denominator


def round_currency(value, decimals: int = 2) -> Optional[float]:
    """Round a value to currency precision."""
    if value is None:
        return None
    return round(float(value), decimals)


# =============================================================================
# Query Utilities
# =============================================================================

def parse_int(value, default: Optional[int] = None) -> Optional[int]:
    """Safely parse an integer from various types."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float(value, default: Optional[float] = None) -> Optional[float]:
    """Safely parse a float from various types."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
