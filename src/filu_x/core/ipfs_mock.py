"""Mock-IPFS moduuli alpha-vaiheeseen – ei vaadi IPFS-daemonia"""
from pathlib import Path
import hashlib
import json
from typing import Dict, Optional

class MockIPFSClient:
    """Simuloi IPFS-toiminnallisuutta paikallisella cachella"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "ipfs_mock"
        self.index_path = self.cache_dir / "index.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, str]:
        """Lataa CID → polku -mapping"""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        """Tallenna index.json"""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2)
    
    def _calculate_cid(self, content: bytes) -> str:
        """Generoi SHA256-hash "CID:nä" (IPFS-vastaava mock)"""
        sha = hashlib.sha256(content).hexdigest()
        return f"Qm{sha[:44]}"
    
    def add_bytes(self, content: bytes, filename: str = "unknown") -> str:
        """Lisää sisältö mock-IPFS:iin ja palauta "CID" """
        cid = self._calculate_cid(content)
        path = self.cache_dir / cid
        
        if not path.exists():
            with open(path, "wb") as f:
                f.write(content)
            self.index[cid] = str(path.relative_to(self.cache_dir))
            self._save_index()
        
        return cid
    
    def add_file(self, path: Path) -> str:
        """Lisää tiedosto mock-IPFS:iin"""
        with open(path, "rb") as f:
            content = f.read()
        return self.add_bytes(content, filename=path.name)
    
    def cat(self, cid: str) -> Optional[bytes]:
        """Hae sisältö CID:llä"""
        if cid not in self.index:
            return None
        path = self.cache_dir / self.index[cid]
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return f.read()
    
    def pin_add(self, cid: str) -> bool:
        """Simuloi pinning-toimintoa"""
        return cid in self.index
    
    def get_gateway_url(self, cid: str) -> str:
        """Palauta "gateway"-URL mock-sisällölle"""
        return f"http://localhost:8080/ipfs/{cid}"

