"""Storage layout for Filu-X file-based architecture with protocol-specific directories and thread support"""
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
        self.public_http_dir = self.public_dir / "http"  # HTTP protocol
        
        # Cached (organized by protocol and user)
        self.cached_dir = self.base_path / "cached"
        self.cached_ipfs_dir = self.cached_dir / "ipfs"
        self.cached_usb_dir = self.cached_dir / "usb"
        self.cached_http_dir = self.cached_dir / "http"  # HTTP cache
        self.cached_threads_dir = self.cached_dir / "threads"
        
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
            self.public_ipfs_dir / "threads",
            self.public_usb_dir / "posts",
            self.public_usb_dir / "blobs",
            self.public_usb_dir / "threads",
            self.public_http_dir / "posts",      # HTTP posts
            self.public_http_dir / "blobs",       # HTTP blobs
            self.public_http_dir / "threads",     # HTTP threads
            self.cached_ipfs_dir / "follows",
            self.cached_usb_dir / "follows",
            self.cached_http_dir / "follows",     # HTTP cache
            self.cached_threads_dir,
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
        elif protocol == "http":
            return self.public_http_dir / "profile.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def manifest_path(self, protocol: str = "ipfs") -> Path:
        """Path to manifest file for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "Filu-X.json"
        elif protocol == "usb":
            return self.public_usb_dir / "Filu-X.json"
        elif protocol == "http":
            return self.public_http_dir / "Filu-X.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def follow_list_path(self, protocol: str = "ipfs") -> Path:
        """Path to follow list JSON for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "follow_list.json"
        elif protocol == "usb":
            return self.public_usb_dir / "follow_list.json"
        elif protocol == "http":
            return self.public_http_dir / "follow_list.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def post_path(self, post_id: str, protocol: str = "ipfs") -> Path:
        """Path to specific post JSON file for specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "posts" / f"{post_id}.json"
        elif protocol == "usb":
            return self.public_usb_dir / "posts" / f"{post_id}.json"
        elif protocol == "http":
            return self.public_http_dir / "posts" / f"{post_id}.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def thread_manifest_path(self, thread_id: str, protocol: str = "ipfs") -> Path:
        """Path to thread manifest file for a specific protocol"""
        if protocol == "ipfs":
            return self.public_ipfs_dir / "threads" / f"{thread_id}.json"
        elif protocol == "usb":
            return self.public_usb_dir / "threads" / f"{thread_id}.json"
        elif protocol == "http":
            return self.public_http_dir / "threads" / f"{thread_id}.json"
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
        elif protocol == "http":
            return self.cached_http_dir / "follows" / safe_username / "profile.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_manifest_path(self, username: str, protocol: str = "ipfs") -> Path:
        """Path to cached manifest for a user"""
        safe_username = self._sanitize_username(username)
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows" / safe_username / "Filu-X.json"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows" / safe_username / "Filu-X.json"
        elif protocol == "http":
            return self.cached_http_dir / "follows" / safe_username / "Filu-X.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_post_path(self, username: str, post_cid: str, protocol: str = "ipfs") -> Path:
        """Path to cached post for a user"""
        safe_username = self._sanitize_username(username)
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows" / safe_username / "posts" / f"{post_cid}.json"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows" / safe_username / "posts" / f"{post_cid}.json"
        elif protocol == "http":
            return self.cached_http_dir / "follows" / safe_username / "posts" / f"{post_cid}.json"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_follows_dir(self, protocol: str = "ipfs") -> Path:
        """Path to follows cache directory for specific protocol"""
        if protocol == "ipfs":
            return self.cached_ipfs_dir / "follows"
        elif protocol == "usb":
            return self.cached_usb_dir / "follows"
        elif protocol == "http":
            return self.cached_http_dir / "follows"
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    
    def cached_user_dir(self, username: str, protocol: str = "ipfs") -> Path:
        """Path to specific user's cache directory"""
        safe_username = self._sanitize_username(username)
        return self.cached_follows_dir(protocol) / safe_username
    
    # ========== THREAD PATHS ==========
    
    def cached_threads_path(self) -> Path:
        """Path to threads cache directory"""
        return self.cached_threads_dir
    
    def cached_thread_manifest_path(self, thread_id: str) -> Path:
        """Path to cached thread manifest file"""
        return self.cached_threads_dir / f"{thread_id}.json"
    
    def thread_ipns_path(self, thread_id: str) -> Path:
        """Path to file storing thread's IPNS name"""
        return self.cached_threads_dir / f"{thread_id}_ipns.txt"
    
    def thread_ipns_name(self, thread_id: str) -> Optional[str]:
        """Get thread's IPNS name from cache if exists"""
        path = self.thread_ipns_path(thread_id)
        if path.exists():
            return path.read_text().strip()
        return None
    
    def save_thread_ipns(self, thread_id: str, ipns_name: str):
        """Save thread's IPNS name to cache"""
        path = self.thread_ipns_path(thread_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ipns_name)
    
    # ========== PRIVATE PATHS ==========
    
    def private_config_path(self) -> Path:
        return self.private_dir / "private_config.json"
    
    def private_key_path(self) -> Path:
        return self.private_dir / "keys" / "ed25519_private.pem"
    
    def public_key_path(self) -> Path:
        return self.private_dir / "keys" / "ed25519_public.pem"
    
    # ========== PROTOCOL SYNC OPERATIONS ==========
    
    def sync_to_protocol(self, protocol: str = "usb"):
        """Copy all public files from ipfs to another protocol"""
        source = self.public_ipfs_dir
        
        if protocol == "usb":
            target = self.public_usb_dir
        elif protocol == "http":
            target = self.public_http_dir
        else:
            raise ValueError(f"Unknown target protocol: {protocol}")
        
        if not source.exists():
            return
        
        shutil.copytree(source, target, dirs_exist_ok=True)
        print(f"✅ Files copied to {protocol} directory: {target}")
    
    def sync_from_protocol(self, username: str, protocol: str = "usb", copy_blobs: bool = False):
        """Copy cached files from protocol cache to main cache"""
        if protocol == "usb":
            source_base = self.cached_usb_dir
        elif protocol == "http":
            source_base = self.cached_http_dir
        else:
            source_base = self.cached_ipfs_dir
        
        source = source_base / "follows" / self._sanitize_username(username)
        target = self.cached_ipfs_dir / "follows" / self._sanitize_username(username)
        
        if not source.exists():
            return
        
        shutil.copytree(source, target, dirs_exist_ok=True)
        print(f"✅ Files copied from {protocol} cache: {source} → {target}")
    
    # ========== UTILITY METHODS ==========
    
    def list_cached_users(self, protocol: str = "ipfs") -> List[str]:
        """List all usernames that have cached content from specific protocol"""
        if protocol == "ipfs":
            cache_dir = self.cached_ipfs_dir
        elif protocol == "usb":
            cache_dir = self.cached_usb_dir
        elif protocol == "http":
            cache_dir = self.cached_http_dir
        else:
            return []
        
        follows_dir = cache_dir / "follows"
        if not follows_dir.exists():
            return []
        return [d.name for d in follows_dir.glob("*") if d.is_dir()]
    
    def list_own_posts(self, protocol: str = "ipfs") -> List[Path]:
        """List all own post files"""
        if protocol == "ipfs":
            posts_dir = self.public_ipfs_dir / "posts"
        elif protocol == "usb":
            posts_dir = self.public_usb_dir / "posts"
        elif protocol == "http":
            posts_dir = self.public_http_dir / "posts"
        else:
            return []
        
        if not posts_dir.exists():
            return []
        return sorted(posts_dir.glob("*.json"), reverse=True)
    
    def list_threads(self, protocol: str = "ipfs") -> List[str]:
        """List all thread manifest IDs"""
        if protocol == "ipfs":
            threads_dir = self.public_ipfs_dir / "threads"
        elif protocol == "usb":
            threads_dir = self.public_usb_dir / "threads"
        elif protocol == "http":
            threads_dir = self.public_http_dir / "threads"
        else:
            return []
        
        if not threads_dir.exists():
            return []
        return [f.stem for f in threads_dir.glob("*.json")]
    
    def get_disk_usage(self) -> int:
        """Calculate total disk usage in bytes"""
        total = 0
        if self.base_path.exists():
            for path in self.base_path.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    total += path.stat().st_size
        return total
    
    # ========== JSON UTILITIES ==========
    
    def load_json(self, path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_json(self, path: Path, data: dict, private: bool = False):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def file_exists(self, path: Path) -> bool:
        return path.exists()
    
    def __str__(self) -> str:
        return f"FiluXStorageLayout(base_path={self.base_path})"
