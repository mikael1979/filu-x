"""Resolve and verify Filu-X content from fx:// or ipns:// links"""
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
from urllib.parse import urlparse, parse_qs

from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import verify_signature
from filu_x.core.ipns import IPNSManager

class ResolutionError(Exception):
    """Content could not be resolved"""
    pass

class SecurityError(Exception):
    """Content failed security checks"""
    pass

class LinkResolver:
    """Parse fx:// and ipns:// links and resolve content"""
    
    PROTOCOL = "fx"
    IPNS_PROTOCOL = "ipns"
    
    def __init__(self, ipfs_client: Optional[IPFSClient] = None, cache_dir: Optional[Path] = None):
        self.ipfs = ipfs_client or IPFSClient(mode="auto")
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "resolved"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ipns = IPNSManager(use_mock=True)  # Alpha uses mock mode
        self.verbose = False
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output"""
        self.verbose = verbose
    
    def parse_link(self, link: str) -> Dict[str, str]:
        """
        Parse fx:// or ipns:// link into components.
        
        Returns dict with keys:
          - protocol: "fx" or "ipns"
          - identifier: CID or IPNS name
          - params: query parameters
        """
        if link.startswith(f"{self.PROTOCOL}://"):
            protocol = self.PROTOCOL
            rest = link[len(f"{self.PROTOCOL}://"):]
        elif link.startswith(f"{self.IPNS_PROTOCOL}://"):
            protocol = self.IPNS_PROTOCOL
            rest = link[len(f"{self.IPNS_PROTOCOL}://"):]
        else:
            raise ValueError(f"Invalid protocol. Expected '{self.PROTOCOL}://' or '{self.IPNS_PROTOCOL}://' prefix")
        
        if "?" in rest:
            identifier_part, query_part = rest.split("?", 1)
        else:
            identifier_part, query_part = rest, ""
        
        identifier = identifier_part.strip()
        
        # Validate identifier format (basic check)
        if protocol == self.PROTOCOL and not re.match(r'^[a-zA-Z0-9]{46,}$', identifier):
            raise ValueError(f"Invalid CID format: {identifier}")
        
        params = {}
        if query_part:
            parsed = parse_qs(query_part)
            params = {k: v[0] for k, v in parsed.items()}
        
        return {
            "protocol": protocol,
            "identifier": identifier,
            "author_hint": params.get("author", ""),
            "type_hint": params.get("type", "unknown")
        }
    
    def resolve_content(self, identifier: str, skip_cache: bool = False, expected_pubkey: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve content by CID or IPNS name.
        
        If identifier starts with 'ipns://', resolve IPNS name first.
        
        Args:
            identifier: CID or IPNS:// URL
            skip_cache: If True, bypass cache and fetch fresh
            expected_pubkey: Optional pubkey for manifest verification
        
        Returns:
            Parsed content as dictionary
        """
        original_identifier = identifier
        
        # Handle IPNS resolution
        if identifier.startswith(f"{self.IPNS_PROTOCOL}://"):
            ipns_name = identifier[len(f"{self.IPNS_PROTOCOL}://"):]
            if self.verbose:
                print(f"   🔍 Resolving IPNS: {ipns_name[:16]}...")
            
            # Resolve IPNS to CID - this is mock in alpha
            cid = self.ipns.resolve(ipns_name)
            if not cid:
                raise ResolutionError(f"Could not resolve IPNS name: {ipns_name[:16]}...")
            
            if self.verbose:
                print(f"   🔍 IPNS -> CID: {cid[:16]}...")
        else:
            cid = identifier
        
        # 1. Check cache first (vain jos skip_cache=False)
        if not skip_cache:
            cached = self._load_from_cache(cid)
            if cached:
                if self.verbose:
                    print(f"   📦 Using cached content: {cid[:16]}...")
                return cached
        elif self.verbose:
            print(f"   📦 Skipping cache (forced fresh fetch)")
        
        # 2. Fetch from IPFS/mock
        if self.verbose:
            print(f"   📥 Fetching from IPFS: {cid[:16]}...")
        
        content_bytes = self.ipfs.cat(cid)
        if content_bytes is None:
            raise ResolutionError(f"Content not found for CID: {cid}")
        
        # 3. Parse JSON
        try:
            content = json.loads(content_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ResolutionError(f"Invalid JSON: {e}")
        
        # 4. Determine content type and verify accordingly
        if self._is_manifest(content):
            # Manifest verification requires expected_pubkey
            if expected_pubkey:
                if "signature" not in content:
                    raise SecurityError(f"Manifest missing signature field")
                
                # Verify signature using provided pubkey
                try:
                    pubkey_bytes = bytes.fromhex(expected_pubkey)
                except ValueError:
                    raise SecurityError(f"Invalid pubkey format: {expected_pubkey[:12]}...")
                
                if not verify_signature(content, content["signature"], pubkey_bytes):
                    raise SecurityError(f"Invalid signature for manifest: {cid}")
                
                content["_validated_type"] = "manifest"
                if self.verbose:
                    print(f"   ✅ Manifest verified")
                
            else:
                # Alpha fallback: accept manifest without verification (with warning)
                if self.verbose:
                    print(f"   ⚠️  Alpha warning: Manifest accepted without signature verification")
                content["_validated_type"] = "manifest (unverified)"
        
        elif "pubkey" in content:
            # Post or profile – verify signature using embedded pubkey
            if "signature" not in content:
                raise SecurityError(f"Content missing signature field")
            
            signature = content["signature"]
            pubkey_hex = content.get("pubkey")
            
            try:
                pubkey_bytes = bytes.fromhex(pubkey_hex)
            except ValueError:
                raise SecurityError(f"Invalid pubkey format: {pubkey_hex[:12]}...")
            
            if not verify_signature(content, signature, pubkey_bytes):
                raise SecurityError(f"Invalid signature for CID: {cid}")
            
            content["_validated_type"] = content.get("type", "post")
            if self.verbose:
                print(f"   ✅ Signature verified")
        
        else:
            # Unknown content type (no pubkey, not manifest) – reject
            raise SecurityError(f"Content type unknown (missing pubkey and not a manifest)")
        
        # 5. Cache for future use
        if not skip_cache:
            self._save_to_cache(cid, content)
        
        return content
    
    def _is_manifest(self, content: Dict[str, Any]) -> bool:
        """Detect if content is a manifest (has 'entries' array and 'author')"""
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
        # Strip signature for cache to save space (optional)
        safe_content = {k: v for k, v in content.items() if k != "signature"}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(safe_content, f, indent=2, ensure_ascii=False)
