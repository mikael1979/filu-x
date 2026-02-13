# filu_x/core/content_validator.py
from typing import Literal, Optional
import magic
import re

# === SAFE CONTENT TYPES (allow by default) ===
SAFE_TYPES = {
    # Images
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "image/bmp", "image/tiff", "image/x-icon",
    
    # Video
    "video/mp4", "video/webm", "video/quicktime",
    "video/x-msvideo", "video/x-matroska", "video/x-flv",
    
    # Audio
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/flac",
    "audio/aac", "audio/mp4",
    
    # Documents
    "text/plain", "application/pdf", "text/csv",
    "application/json", "application/xml", "application/yaml",
    "application/toml",
    
    # Fonts
    "font/ttf", "font/woff", "font/woff2", "font/otf",
}

# === GRAY AREA (require sanitization) ===
GRAY_TYPES = {
    "text/html": "sanitize_html",
    "image/svg+xml": "sanitize_svg",
    "text/markdown": "sanitize_markdown",
    "text/css": "sanitize_css",
}

# === DANGEROUS TYPES (block by default) ===
DANGEROUS_PATTERNS = [
    # Code execution
    r"\.js$", r"\.mjs$", r"\.cjs$", r"\.py$", r"\.pyc$", r"\.pyo$",
    r"\.sh$", r"\.bash$", r"\.zsh$", r"\.php$", r"\.rb$", r"\.pl$",
    r"\.ps1$", r"\.bat$", r"\.cmd$", r"\.exe$", r"\.dll$", r"\.so$",
    r"\.bin$", r"\.elf$", r"\.wasm$", r"\.jar$", r"\.class$",
    r"\.vbs$", r"\.vbe$",
    
    # Active web content
    r"\.xhtml$", r"\.hta$",
    
    # Archives (require scanning)
    r"\.zip$", r"\.tar$", r"\.gz$", r"\.bz2$", r"\.7z$", r"\.rar$",
    r"\.iso$",
]

class ContentValidator:
    """Validate and sanitize content based on type"""
    
    def __init__(self, allow_archives: bool = False):
        self.allow_archives = allow_archives
    
    def validate_mime_type(self, content: bytes, declared_type: Optional[str] = None) -> str:
        """
        Validate MIME type using both declared type and content inspection.
        Returns validated MIME type or raises SecurityError.
        """
        # 1. Inspect actual content (most reliable)
        detected_type = magic.from_buffer(content, mime=True)
        
        # 2. If declared type exists, verify it matches
        if declared_type:
            if declared_type != detected_type:
                raise SecurityError(
                    f"Declared type '{declared_type}' doesn't match actual type '{detected_type}'"
                )
        
        # 3. Check against dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, detected_type, re.IGNORECASE):
                raise SecurityError(f"Blocked dangerous content type: {detected_type}")
        
        # 4. Classify and handle
        if detected_type in SAFE_TYPES:
            return detected_type
        
        elif detected_type in GRAY_TYPES:
            return detected_type  # Will be sanitized later
        
        else:
            raise SecurityError(f"Unknown/untrusted content type: {detected_type}")
    
    def requires_sanitization(self, mime_type: str) -> bool:
        """Check if content type requires sanitization"""
        return mime_type in GRAY_TYPES
    
    def get_sanitization_method(self, mime_type: str):
        """Get appropriate sanitization method"""
        return GRAY_TYPES.get(mime_type)
