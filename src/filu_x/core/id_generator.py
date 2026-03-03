"""Deterministic ID generation for posts and profiles"""
import hashlib
from datetime import datetime
import re
from typing import Optional

def generate_post_id(pubkey: str, timestamp: str, content: str) -> str:
    """
    Generate deterministic post ID using SHA-256 hash of:
      pubkey (normalized) + timestamp (ISO8601) + content (normalized)
    
    NEVER includes display name – identity is cryptographic, not social.
    
    Returns 32-character hex string (first 128 bits of SHA-256).
    """
    # Normalize inputs to prevent canonicalization attacks
    normalized_pubkey = pubkey.strip().lower()
    normalized_timestamp = timestamp.strip()
    normalized_content = content.strip()
    
    # Concatenate for hash
    data = f"{normalized_pubkey}{normalized_timestamp}{normalized_content}"
    
    # SHA-256 hash
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    full_hash = hash_obj.hexdigest()
    
    # Return first 32 chars (128 bits – sufficient for global uniqueness)
    return full_hash[:32]

def generate_local_id(post_hash: str, manifest_version: str, custom_name: str = None, post_number: int = None) -> str:
    """
    Generate a human-friendly local ID that includes manifest version and post hash.
    
    Format: {name}.{manifest_version}_{post_hash_6chars}
    
    Args:
        post_hash: Full post hash (32 chars)
        manifest_version: Manifest version string (e.g. "0.0.0.42")
        custom_name: User-provided name (optional)
        post_number: Auto-generated post number (optional)
    
    Returns:
        Local ID in format: {name}.{manifest_version}_{post_hash_6chars}
    """
    # Take first 6 characters of post hash for fingerprint
    post_fingerprint = post_hash[:6]
    
    # Clean manifest version (replace dots with underscores for filesystem safety)
    clean_version = manifest_version.replace('.', '_')
    
    # Determine the name part
    if custom_name:
        # Sanitize custom name
        safe_name = custom_name.strip().lower()
        safe_name = re.sub(r'[^a-z0-9]+', '-', safe_name)
        safe_name = safe_name.strip('-')
        name_part = safe_name
    elif post_number is not None:
        name_part = f"post{post_number}"
    else:
        name_part = "post"
    
    return f"{name_part}.{clean_version}_{post_fingerprint}"

def parse_local_id(local_id: str) -> dict:
    """
    Parse a local ID into its components.
    
    Format: {name}.{manifest_version}_{post_hash_6chars}
    
    Returns:
        Dict with keys: name, manifest_version, post_fingerprint
    """
    # Match pattern: name.version_hash
    pattern = r'^(.+)\.([0-9_]+)_([a-f0-9]{6})$'
    match = re.match(pattern, local_id)
    
    if match:
        name, version, fingerprint = match.groups()
        # Convert underscores back to dots for version
        manifest_version = version.replace('_', '.')
        return {
            "name": name,
            "manifest_version": manifest_version,
            "post_fingerprint": fingerprint
        }
    
    return None

def normalize_display_name(display_name: str) -> str:
    """
    Normalize display name for collision detection (not used in ID generation).
    
    Rules:
      - Strip @ prefix/suffix
      - Lowercase
      - Remove extra whitespace
    """
    name = display_name.strip()
    if name.startswith("@"):
        name = name[1:]
    if name.endswith("@"):
        name = name[:-1]
    return name.lower()

def detect_display_name_collision(
    display_name: str,
    pubkey: str,
    existing_follows: list
) -> Optional[dict]:
    """
    Detect if display name collides with already followed users.
    
    Returns collision info dict if collision exists, None otherwise.
    
    Collision = same normalized display name but different pubkey.
    """
    normalized = normalize_display_name(display_name)
    
    for follow in existing_follows:
        existing_name = normalize_display_name(follow.get("user", ""))
        existing_pubkey = follow.get("pubkey", "")
        
        if normalized == existing_name and existing_pubkey != pubkey:
            return {
                "existing_user": follow.get("user", "unknown"),
                "existing_pubkey_suffix": existing_pubkey[:12] + "...",
                "new_pubkey_suffix": pubkey[:12] + "..."
            }
    
    return None
