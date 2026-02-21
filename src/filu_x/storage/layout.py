"""Storage layout for Filu-X file-based architecture with protocol-specific directories"""
from pathlib import Path
from typing import Optional, List
import json
import os
import shutil

class FiluXStorageLayout:
    """Manages directory structure for Filu-X data storage"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize storage layout.
        
        If base_path is provided, use it.
        Otherwise, use default: ./data/ in current working directory
        """
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            self.base_path = Path.cwd() / "data"
        
        # Private (never shared)
        self.private_dir = self.base_path / "user_private"
        
        # Public (organized by protocol)
        self.public_dir = self.base_path / "public"
        self.public_ipfs_dir = self.public_dir / "ipfs"
        self.public_usb_dir = self.public_dir / "usb"
        
        # Cached (organized by protocol and user)
        self.cached_dir = self.base_path / "cached"
        self.cached_ipfs_dir = self.cached_dir / "ipfs"
        self.cached_usb_dir = self.cached_dir / "usb"
        
        # Blobs for large files (images, videos, etc.)
        self.blobs_dir = self.base_path / "blobs"
        self.blobs_videos_dir = self.blobs_dir / "videos"
        self.blobs_images_dir = self.blobs_dir / "images"
        self.blobs_audio_dir = self.blobs_dir / "audio"
        self.blobs_other_dir = self.blobs_dir / "other"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create essential directories if they don't exist"""
        for path in [
            self.private_dir / "keys",
            self.private_dir / "sessions",
            self.public_ipfs_dir / "posts",
            self.public_ipfs_dir / "blobs",
            self.public_usb_dir / "posts",
            self.public_usb_dir / "blobs",
            self.cached_ipfs_dir / "follows",
            self.cached_usb_dir / "follows",
            self.cached_dir / "threads",
            self.blobs_videos_dir,
            self.blobs_images_dir,
            self.blobs_audio_dir,
            self.blobs_other_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    # ========== PATHS FOR OWN CONTENT ==========
    
    def profile_path(self, protocol: str = "ipfs") -> Path:
        """Path to user's public profile JSON for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "profile.json"
        elif protocol == "usb":
            return self.public_usb_dir / "profile.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def manifest_path(self, protocol: str = "ipfs") -> Path:
        """Path to manifest file for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "Filu-X.json"
        elif protocol == "usb":
            return self.public_usb_dir / "Filu-X.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def follow_list_path(self, protocol: str = "ipfs") -> Path:
        """Path to follow list JSON for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "follow_list.json"
        elif protocol == "usb":
            return self.public_usb_dir / "follow_list.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def post_path(self, post_id: str, protocol: str = "ipfs") -> Path:
        """Path to specific post JSON file for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "posts" / f"{post_id}.json"
        elif protocol == "usb":
            return self.public_usb_dir / "posts" / f"{post_id}.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def blob_path(self, blob_cid: str, blob_type: str = "other") -> Path:
        """Path to blob file (images, videos, etc.)"""
        type_map = {
            "video": self.blobs_videos_dir,
            "image": self.blobs_images_dir,
            "audio": self.blobs_audio_dir,
        }
        base_dir = type_map.get(blob_type, self.blobs_other_dir)
        
        # Use first two characters as subdirectory to avoid too many files
        subdir = blob_cid[:2] if len(blob_cid) > 2 else "xx"
        return base_dir / subdir / blob_cid
    
    # ========== PATHS FOR CACHED CONTENT ==========
    
    def _sanitize_username(self, username: str) -> str:
        """Sanitize username for filesystem safety"""
        return (username
                .replace("@", "")
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(".", "_"))
    
    def cached_profile_path(self, username: str, protocol: str = "ipfs") -> Path:
        """Path to cached profile for a user"""
        safe_username = self._sanitize_username(username)
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows" / safe_username / "profile.json"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows" / safe_username / "profile.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_manifest_path(self, username: str, protocol: str = "ipfs") -> Path:
        """Path to cached manifest for a user"""
        safe_username = self._sanitize_username(username)
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows" / safe_username / "Filu-X.json"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows" / safe_username / "Filu-X.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_post_path(self, username: str, post_cid: str, protocol: str = "ipfs") -> Path:
        """Path to cached post for a user"""
        safe_username = self._sanitize_username(username)
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows" / safe_username / "posts" / f"{post_cid}.json"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows" / safe_username / "posts" / f"{post_cid}.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_follows_dir(self, protocol: str = "ipfs") -> Path:
        """Path to follows cache directory for specific protocol"""
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_user_dir(self, username: str, protocol: str = "ipfs") -> Path:
        """Path to specific user's cache directory"""
        safe_username = self._sanitize_username(username)
        return self.cached_follows_dir(protocol) / safe_username
    
    def thread_cache_path(self, thread_id: str) -> Path:
        """Path to thread cache file"""
        path = self.cached_dir / "threads" / f"{thread_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    # ========== PRIVATE PATHS ==========
    
    def private_config_path(self) -> Path:
        """Path to private configuration JSON"""
        return self.private_dir / "private_config.json"
    
    def private_key_path(self) -> Path:
        """Path to Ed25519 private key"""
        return self.private_dir / "keys" / "ed25519_private.pem"
    
    def public_key_path(self) -> Path:
        """Path to Ed25519 public key"""
        return self.private_dir / "keys" / "ed25519_public.pem"
    
    # ========== PROTOCOL SYNC OPERATIONS ==========
    
    def sync_to_protocol(self, protocol: str = "usb"):
        """
        Copy all public files from ipfs to another protocol (e.g., usb)
        
        For blob files, creates symbolic links by default.
        Use copy_blobs=True to copy actual files instead of symlinks.
        """
        source = self.public_ipfs_dir
        target = self.public_usb_dir if protocol == "usb" else self.public_ipfs_dir
        
        if not source.exists():
            return
        
        # Copy all files recursively
        shutil.copytree(source, target, dirs_exist_ok=True)
        
        # For blobs, we could create symlinks instead of copies
        blobs_target = target / "blobs"
        if blobs_target.exists():
            shutil.rmtree(blobs_target)
        
        # Create symlinks to actual blob files
        blobs_target.mkdir(parents=True, exist_ok=True)
        for blob_type_dir in [self.blobs_videos_dir, self.blobs_images_dir, 
                              self.blobs_audio_dir, self.blobs_other_dir]:
            if blob_type_dir.exists():
                for subdir in blob_type_dir.glob("*"):
                    if subdir.is_dir():
                        for blob_file in subdir.glob("*"):
                            rel_path = blob_file.relative_to(self.blobs_dir)
                            link_path = blobs_target / rel_path
                            link_path.parent.mkdir(parents=True, exist_ok=True)
                            if not link_path.exists():
                                os.symlink(blob_file, link_path)
    
    def sync_from_protocol(self, username: str, protocol: str = "usb", copy_blobs: bool = False):
        """
        Copy cached files from protocol cache to main cache
        
        Args:
            username: Username to sync
            protocol: Source protocol ("usb" or "ipfs")
            copy_blobs: If True, copy blob files; if False, create symlinks
        """
        source_base = self.cached_usb_dir if protocol == "usb" else self.cached_ipfs_dir
        source = source_base / "follows" / self._sanitize_username(username)
        target = self.cached_ipfs_dir / "follows" / self._sanitize_username(username)
        
        if not source.exists():
            return
        
        # Copy all files recursively
        shutil.copytree(source, target, dirs_exist_ok=True)
        
        # Handle blobs if present
        source_blobs = source / "blobs"
        target_blobs = target / "blobs"
        
        if source_blobs.exists() and target_blobs.exists():
            if copy_blobs:
                # Copy actual blob files
                shutil.copytree(source_blobs, target_blobs, dirs_exist_ok=True)
            else:
                # Create symlinks to blob files in main blob storage
                for blob_file in source_blobs.rglob("*"):
                    if blob_file.is_file():
                        # Extract blob_cid from path
                        # Assuming path like: .../blobs/videos/ab/abc123...
                        rel_path = blob_file.relative_to(source_blobs)
                        target_link = target_blobs / rel_path
                        target_link.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Find actual blob in main blob storage
                        # This assumes blob storage structure matches
                        actual_blob = self.blobs_dir / rel_path
                        if actual_blob.exists() and not target_link.exists():
                            os.symlink(actual_blob, target_link)
    
    # ========== UTILITY METHODS ==========
    
    def list_cached_users(self, protocol: str = "ipfs") -> List[str]:
        """List all usernames that have cached content from specific protocol"""
        cache_dir = self.cached_ipfs_dir if protocol == "ipfs" else self.cached_usb_dir
        follows_dir = cache_dir / "follows"
        if not follows_dir.exists():
            return []
        return [d.name for d in follows_dir.glob("*") if d.is_dir()]
    
    def list_own_posts(self, protocol: str = "ipfs") -> List[Path]:
        """List all own post files"""
        posts_dir = self.public_ipfs_dir / "posts" if protocol == "ipfs" else self.public_usb_dir / "posts"
        if not posts_dir.exists():
            return []
        return sorted(posts_dir.glob("*.json"), reverse=True)
    
    def get_disk_usage(self) -> int:
        """Calculate total disk usage in bytes"""
        total = 0
        if self.base_path.exists():
            for path in self.base_path.rglob("*"):
                if path.is_file() and not path.is_symlink():  # Don't count symlinks twice
                    total += path.stat().st_size
        return total
    
    # ========== JSON UTILITIES ==========
    
    def load_json(self, path: Path) -> dict:
        """Load JSON file safely"""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_json(self, path: Path, data: dict, private: bool = False):
        """Save dictionary as JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def file_exists(self, path: Path) -> bool:
        """Check if file exists"""
        return path.exists()
    
    def __str__(self) -> str:
        """String representation"""
        return f"FiluXStorageLayout(base_path={self.base_path})"
