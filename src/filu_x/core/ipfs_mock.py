"""Mock IPFS module for alpha phase – no IPFS daemon required"""
from pathlib import Path
import hashlib
import json
from typing import Dict, Optional

class MockIPFSClient:
    """Simulate IPFS functionality with local cache"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "ipfs_mock"
        self.index_path = self.cache_dir / "index.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, str]:
        """Load CID → path mapping"""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        """Save index.json"""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2)
    
    def _calculate_cid(self, content: bytes) -> str:
        """Generate SHA256 hash as "CID" (IPFS-like mock)"""
        sha = hashlib.sha256(content).hexdigest()
        return f"Qm{sha[:44]}"
    
    def add_bytes(self, content: bytes, filename: str = "unknown") -> str:
        """Add content to mock IPFS and return "CID" """
        cid = self._calculate_cid(content)
        path = self.cache_dir / cid
        
        if not path.exists():
            with open(path, "wb") as f:
                f.write(content)
            self.index[cid] = str(path.relative_to(self.cache_dir))
            self._save_index()
        
        return cid
    
    def add_file(self, path: Path) -> str:
        """Add file to mock IPFS"""
        with open(path, "rb") as f:
            content = f.read()
        return self.add_bytes(content, filename=path.name)
    
    def cat(self, cid: str) -> Optional[bytes]:
        """Retrieve content by CID"""
        if cid not in self.index:
            return None
        path = self.cache_dir / self.index[cid]
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return f.read()
    
    def pin_add(self, cid: str) -> bool:
        """Simulate pinning operation"""
        return cid in self.index
    
    def get_gateway_url(self, cid: str) -> str:
        """Return "gateway" URL for mock content"""
        return f"http://localhost:8080/ipfs/{cid}"
