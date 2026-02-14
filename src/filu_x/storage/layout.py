"""Storage layout for Filu-X file-based architecture"""
from pathlib import Path
from typing import Optional
import json

class FiluXStorageLayout:
    """Manages directory structure for Filu-X data storage"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".local" / "share" / "filu-x"
        self.private_dir = self.base_path / "data" / "user_private"
        self.public_dir = self.base_path / "data" / "public"
        self.posts_dir = self.public_dir / "posts"
        self.cached_dir = self.base_path / "data" / "cached"  # NEW: cached content
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create essential directories if they don't exist"""
        for path in [
            self.private_dir / "keys",
            self.private_dir / "sessions",
            self.posts_dir,
            self.cached_dir / "follows",  # NEW: follows cache
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    # Public paths
    def profile_path(self) -> Path:
        """Path to user's public profile JSON"""
        return self.public_dir / "profile.json"
    
    def manifest_path(self) -> Path:
        """Path to manifest file (list of publishable files)"""
        return self.public_dir / "Filu-X.json"
    
    def follow_list_path(self) -> Path:
        """Path to follow list JSON"""
        return self.public_dir / "follow_list.json"
    
    def post_path(self, post_id: str) -> Path:
        """Path to specific post JSON file"""
        return self.posts_dir / f"{post_id}.json"
    
    # Private paths
    def private_config_path(self) -> Path:
        """Path to private configuration JSON"""
        return self.private_dir / "private_config.json"
    
    def private_key_path(self) -> Path:
        """Path to Ed25519 private key (PEM format)"""
        return self.private_dir / "keys" / "ed25519_private.pem"
    
    def public_key_path(self) -> Path:
        """Path to Ed25519 public key (PEM format)"""
        return self.private_dir / "keys" / "ed25519_public.pem"
    
    # Cached paths (NEW)
    def cached_base_path(self) -> Path:
        """Base path for cached content from followed users"""
        return self.cached_dir
    
    def cached_follows_path(self) -> Path:
        """Path to follows cache directory"""
        return self.cached_dir / "follows"
    
    def cached_user_path(self, username: str) -> Path:
        """
        Path to specific user's cache directory.
        
        Args:
            username: User display name (e.g., "@alice" or "alice")
        
        Returns:
            Path to user's cache directory (sanitized filename)
        """
        # Sanitize username for filesystem safety
        safe_username = (
            username
            .replace("@", "")
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(".", "_")
        )
        path = self.cached_follows_path() / safe_username
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # JSON utilities
    def load_json(self, path: Path) -> dict:
        """
        Load JSON file safely.
        
        Args:
            path: Path to JSON file
        
        Returns:
            Parsed JSON as dictionary
        
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_json(self, path: Path, data: dict, private: bool = False):
        """
        Save dictionary as JSON file.
        
        Args:
            path: Destination path
            data: Dictionary to serialize
            private: Hint that data contains private information (not enforced)
        """
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with pretty formatting
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
