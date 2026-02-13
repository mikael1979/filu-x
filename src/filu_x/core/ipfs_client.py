"""IPFS client using raw HTTP API (compatible with kubo v0.38+)"""
from pathlib import Path
from typing import Optional, Literal
import hashlib
import json
import requests
from requests.exceptions import ConnectionError, Timeout

class IPFSClient:
    """
    Unified IPFS client using HTTP API.
    Falls back to mock mode if daemon is unavailable.
    """
    
    def __init__(
        self,
        mode: Literal["auto", "real", "mock"] = "auto",
        api_url: str = "http://127.0.0.1:5001/api/v0",
        timeout: int = 10,
        cache_dir: Optional[Path] = None
    ):
        self.mode = mode
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "ipfs_mock"
        self.use_real = False
        
        # Testaa yhteys IPFS daemoniin
        if mode in ["auto", "real"]:
            try:
                response = requests.post(
                    f"{self.api_url}/id",
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    self.use_real = True
                    print(f"✅ Connected to IPFS daemon ({self.api_url})")
                else:
                    raise ConnectionError(f"IPFS returned status {response.status_code}")
            except Exception as e:
                if mode == "real":
                    raise RuntimeError(f"Failed to connect to IPFS daemon: {e}")
                print(f"⚠️  IPFS daemon not available ({e}), using mock mode")
                self.use_real = False
        else:
            self.use_real = False
    
    def add_bytes(self, content: bytes, filename: str = "unknown") -> str:
        """Add content to IPFS and return CID"""
        if self.use_real:
            try:
                files = {"file": (filename, content)}
                response = requests.post(
                    f"{self.api_url}/add",
                    files=files,
                    params={"cid-version": 1, "pin": True},
                    timeout=self.timeout * 2  # Lisää aikaa suurelle sisällölle
                )
                response.raise_for_status()
                result = response.json()
                return result["Hash"]
            except Exception as e:
                print(f"⚠️  IPFS add failed ({e}), falling back to mock")
                return self._mock_add_bytes(content, filename)
        else:
            return self._mock_add_bytes(content, filename)
    
    def add_file(self, path: Path) -> str:
        """Add file to IPFS and return CID"""
        if self.use_real:
            try:
                with open(path, "rb") as f:
                    files = {"file": (path.name, f)}
                    response = requests.post(
                        f"{self.api_url}/add",
                        files=files,
                        params={"cid-version": 1, "pin": True},
                        timeout=self.timeout * 2
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result["Hash"]
            except Exception as e:
                print(f"⚠️  IPFS add failed ({e}), falling back to mock")
                with open(path, "rb") as f:
                    content = f.read()
                return self._mock_add_bytes(content, path.name)
        else:
            with open(path, "rb") as f:
                content = f.read()
            return self._mock_add_bytes(content, path.name)
    
    def cat(self, cid: str) -> Optional[bytes]:
        """Retrieve content from IPFS by CID"""
        if self.use_real:
            try:
                response = requests.post(
                    f"{self.api_url}/cat",
                    params={"arg": cid},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.content
                return None
            except Exception:
                return None
        else:
            mock_path = self.cache_dir / cid
            if mock_path.exists():
                with open(mock_path, "rb") as f:
                    return f.read()
            return None
    
    def pin_add(self, cid: str) -> bool:
        """Pin content to ensure it's retained"""
        if self.use_real:
            try:
                response = requests.post(
                    f"{self.api_url}/pin/add",
                    params={"arg": cid},
                    timeout=self.timeout
                )
                return response.status_code == 200
            except Exception:
                return False
        else:
            return (self.cache_dir / cid).exists()
    
    def get_gateway_url(self, cid: str) -> str:
        """Get public gateway URL for CID"""
        return f"https://ipfs.io/ipfs/{cid}"
    
    def _mock_add_bytes(self, content: bytes, filename: str) -> str:
        """Mock IPFS implementation (SHA256-based CIDs)"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate SHA256 hash (simulating IPFS CIDv1 for raw leaves)
        sha = hashlib.sha256(content).hexdigest()
        cid = f"Qm{sha[:44]}"  # Simulate base58-encoded CID
        
        # Save to cache
        path = self.cache_dir / cid
        if not path.exists():
            with open(path, "wb") as f:
                f.write(content)
        
        return cid
