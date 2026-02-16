"""Deterministic ID generation for posts and profiles"""
import hashlib
from typing import Optional

def generate_post_id(pubkey: str, timestamp: str, content: str) -> str:
    """
    Generate deterministic post ID using SHA-256 hash of:
      pubkey (normalized) + timestamp (ISO8601) + content (normalized)
    
    NEVER includes display name – identity is cryptographic, not social.
    
    Returns 32-character hex string (first 128 bits of SHA-256).
    
    Example:
      generate_post_id(
        "ed25519:8a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
        "2026-02-16T12:00:00Z",
        "Hello world!"
      )
      → "a1b2c3d4e5f678901234567890abcdef"
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


def normalize_display_name(display_name: str) -> str:
    """
    Normalize display name for collision detection (not used in ID generation).
    
    Rules:
      - Strip @ prefix/suffix
      - Lowercase
      - Remove extra whitespace
    
    Example:
      "@Alice " → "alice"
      "bob" → "bob"
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
