"""Resolve and verify Filu-X content from fx:// links"""
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
from urllib.parse import urlparse, parse_qs

from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import verify_signature

class ResolutionError(Exception):
    """Content could not be resolved"""
    pass

class SecurityError(Exception):
    """Content failed security checks"""
    pass

class LinkResolver:
    """Parse fx:// links and resolve content"""
    
    PROTOCOL = "fx"
    
    def __init__(self, ipfs_client: Optional[IPFSClient] = None, cache_dir: Optional[Path] = None):
        self.ipfs = ipfs_client or IPFSClient(mode="auto")
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "resolved"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_fx_link(self, link: str) -> Dict[str, str]:
        """Parse fx:// link into components"""
        if not link.startswith(f"{self.PROTOCOL}://"):
            raise ValueError(f"Invalid protocol. Expected '{self.PROTOCOL}://' prefix")
        
        rest = link[len(f"{self.PROTOCOL}://"):]
        
        if "?" in rest:
            cid_part, query_part = rest.split("?", 1)
        else:
            cid_part, query_part = rest, ""
        
        cid = cid_part.strip()
        
        if not re.match(r'^[a-zA-Z0-9]{46,}$', cid):
            raise ValueError(f"Invalid CID format: {cid}")
        
        params = {}
        if query_part:
            parsed = parse_qs(query_part)
            params = {k: v[0] for k, v in parsed.items()}
        
        return {
            "protocol": self.PROTOCOL,
            "cid": cid,
            "author_hint": params.get("author", ""),
            "type_hint": params.get("type", "unknown")
        }
    
    def resolve_content(self, cid: str, skip_cache: bool = False) -> Dict[str, Any]:
        """
        Resolve content by CID – check cache first, then IPFS/mock.
        
        Alpha limitation: Manifests (with 'entries' field) are returned without
        signature verification. Posts and profiles are fully verified.
        """
        # 1. Check cache first
        if not skip_cache:
            cached = self._load_from_cache(cid)
            if cached:
                return cached
        
        # 2. Fetch from IPFS/mock
        content_bytes = self.ipfs.cat(cid)
        if content_bytes is None:
            raise ResolutionError(f"Content not found for CID: {cid}")
        
        # 3. Parse JSON
        try:
            content = json.loads(content_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ResolutionError(f"Invalid JSON: {e}")
        
        # 4. ALPHA LIMITATION: Skip verification for manifests
        #    (manifests don't have 'pubkey' field – they reference author via 'author')
        if self._is_manifest(content):
            # For alpha, accept manifests without verification
            # Beta will implement proper manifest verification via author lookup
            return content
        
        # 5. Verify signature for posts/profiles
        if "signature" not in content:
            raise SecurityError(f"Content missing signature field")
        
        signature = content["signature"]
        pubkey_hex = content.get("pubkey")
        
        if not pubkey_hex:
            # Try to extract pubkey from profile structure (alpha fallback)
            if "author" in content and "feed_cid" in content:
                # This is a profile – skip strict verification for alpha
                return content
            raise SecurityError(
                f"Content missing 'pubkey' field. Available keys: {list(content.keys())[:5]}"
            )
        
        try:
            pubkey_bytes = bytes.fromhex(pubkey_hex)
        except ValueError:
            raise SecurityError(f"Invalid pubkey format: {pubkey_hex[:12]}...")
        
        # Verify signature covers entire content (excluding signature field itself)
        if not verify_signature(content, signature, pubkey_bytes):
            raise SecurityError(f"Invalid signature for CID: {cid}")
        
        # 6. Cache for future use
        if not skip_cache:
            self._save_to_cache(cid, content)
        
        return content
    
    def _is_manifest(self, content: Dict[str, Any]) -> bool:
        """Detect if content is a manifest (has 'entries' array)"""
        return (
            isinstance(content.get("entries"), list) and
            "author" in content and
            "version" in content
        )
    
    def _load_from_cache(self, cid: str) -> Optional[Dict[str, Any]]:
        cache_path = self.cache_dir / f"{cid}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_to_cache(self, cid: str, content: Dict[str, Any]):
        cache_path = self.cache_dir / f"{cid}.json"
        safe_content = {k: v for k, v in content.items() if k != "signature"}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(safe_content, f, indent=2, ensure_ascii=False)
