"""Resolve and verify Filu-X content from fx://, ipns://, or http:// links"""
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
import hashlib
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

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
    """Parse fx://, ipns://, and http:// links and resolve content"""
    
    PROTOCOL = "fx"
    IPNS_PROTOCOL = "ipns"
    HTTP_PROTOCOL = "http"
    HTTPS_PROTOCOL = "https"
    
    def __init__(self, ipfs_client: Optional[IPFSClient] = None, cache_dir: Optional[Path] = None):
        self.ipfs = ipfs_client or IPFSClient(mode="auto")
        self.cache_dir = cache_dir or Path.home() / ".cache" / "filu-x" / "resolved"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ipns = IPNSManager(use_mock=True)
        self.verbose = False
        self.session = None  # For HTTP requests
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output"""
        self.verbose = verbose
    
    def _get_http_session(self):
        """Lazy-load HTTP session"""
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Filu-X/0.0.7 (Protocol Test)'
            })
        return self.session
    
    def parse_link(self, link: str) -> Dict[str, str]:
        """
        Parse fx://, ipns://, or http:// link into components.
        
        Returns dict with keys:
          - protocol: "fx", "ipns", "http", or "https"
          - identifier: CID, IPNS name, or URL path
          - params: query parameters
        """
        if link.startswith(f"{self.PROTOCOL}://"):
            protocol = self.PROTOCOL
            rest = link[len(f"{self.PROTOCOL}://"):]
        elif link.startswith(f"{self.IPNS_PROTOCOL}://"):
            protocol = self.IPNS_PROTOCOL
            rest = link[len(f"{self.IPNS_PROTOCOL}://"):]
        elif link.startswith(f"{self.HTTP_PROTOCOL}://"):
            protocol = self.HTTP_PROTOCOL
            rest = link[len(f"{self.HTTP_PROTOCOL}://"):]
        elif link.startswith(f"{self.HTTPS_PROTOCOL}://"):
            protocol = self.HTTPS_PROTOCOL
            rest = link[len(f"{self.HTTPS_PROTOCOL}://"):]
        else:
            raise ValueError(f"Invalid protocol. Expected '{self.PROTOCOL}://', '{self.IPNS_PROTOCOL}://', or 'http://'")
        
        if "?" in rest:
            identifier_part, query_part = rest.split("?", 1)
        else:
            identifier_part, query_part = rest, ""
        
        identifier = identifier_part.strip()
        
        # Validate identifier format for fx://
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
    
    def _fetch_http(self, url: str) -> bytes:
        """Fetch content via HTTP"""
        if self.verbose:
            print(f"   🌐 HTTP GET: {url[:50]}...")
        
        try:
            session = self._get_http_session()
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            if self.verbose:
                print(f"   ✅ HTTP {response.status_code}: {len(response.content)} bytes")
            
            return response.content
            
        except ImportError:
            raise ResolutionError("Requests library not installed. Install with: pip install requests")
        except Exception as e:
            raise ResolutionError(f"HTTP fetch failed: {e}")
    
    def resolve_content(self, identifier: str, skip_cache: bool = False, expected_pubkey: Optional[str] = None, do_verify: bool = True) -> Dict[str, Any]:
        """
        Resolve content by CID, IPNS name, or HTTP URL.
        
        If do_verify is False, skip all signature verification (for testing).
        
        Args:
            identifier: CID, IPNS:// URL, or HTTP URL
            skip_cache: If True, bypass cache and fetch fresh
            expected_pubkey: Optional pubkey for manifest verification
            do_verify: If False, skip signature verification entirely
        
        Returns:
            Parsed content as dictionary with _resolved_cid and _resolved_at fields
        """
        original_identifier = identifier
        resolved_cid = None
        was_ipns = False
        was_http = False
        
        # Handle HTTP URLs
        if identifier.startswith('http://') or identifier.startswith('https://'):
            was_http = True
            content_bytes = self._fetch_http(identifier)
            # Generate a CID-like hash for HTTP content (for caching)
            resolved_cid = hashlib.sha256(content_bytes).hexdigest()
            if self.verbose:
                print(f"   🔑 HTTP content hash: {resolved_cid[:16]}...")
        
        # Handle IPNS
        elif identifier.startswith(f"{self.IPNS_PROTOCOL}://"):
            was_ipns = True
            ipns_name = identifier[len(f"{self.IPNS_PROTOCOL}://"):]
            if self.verbose:
                print(f"   🔍 Resolving IPNS: {ipns_name[:16]}...")
            
            cid = self.ipns.resolve(ipns_name)
            if not cid:
                raise ResolutionError(f"Could not resolve IPNS name: {ipns_name[:16]}...")
            
            if self.verbose:
                print(f"   🔍 IPNS -> CID: {cid[:16]}...")
            resolved_cid = cid
            content_bytes = self.ipfs.cat(cid)
            if content_bytes is None:
                raise ResolutionError(f"Content not found for CID: {cid}")
        
        # Handle direct CID
        else:
            cid = identifier
            resolved_cid = cid
            content_bytes = self.ipfs.cat(cid)
            if content_bytes is None:
                raise ResolutionError(f"Content not found for CID: {cid}")
        
        # Check cache (only if not skip_cache)
        if not skip_cache:
            cached = self._load_from_cache(resolved_cid)
            if cached:
                if self.verbose:
                    print(f"   📦 Using cached content: {resolved_cid[:16]}...")
                return cached
        elif self.verbose:
            print(f"   📦 Skipping cache (forced fresh fetch)")
        
        # Parse JSON
        try:
            content = json.loads(content_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ResolutionError(f"Invalid JSON: {e}")
        
        # Add metadata about how it was resolved
        content["_resolved_from"] = original_identifier
        content["_resolved_cid"] = resolved_cid
        content["_resolved_at"] = datetime.now(timezone.utc).isoformat()
        if was_http:
            content["_resolved_via"] = "http"
        elif was_ipns:
            content["_resolved_via"] = "ipns"
        else:
            content["_resolved_via"] = "ipfs"
        
        # If signature verification is disabled, accept content as-is
        if not do_verify:
            content["_validated_type"] = "unverified"
            if self.verbose:
                print(f"   ⚠️  Signature verification skipped (--allow-unverified)")
            
            # Cache for future use
            if not skip_cache:
                self._save_to_cache(resolved_cid, content)
            
            return content
        
        # Otherwise, verify signatures normally
        if self._is_manifest(content):
            # Manifest verification requires expected_pubkey
            if expected_pubkey:
                if "signature" not in content:
                    raise SecurityError(f"Manifest missing signature field")
                
                try:
                    pubkey_bytes = bytes.fromhex(expected_pubkey)
                except ValueError:
                    raise SecurityError(f"Invalid pubkey format: {expected_pubkey[:12]}...")
                
                if not verify_signature(content, content["signature"], pubkey_bytes):
                    raise SecurityError(f"Invalid signature for manifest: {resolved_cid[:16]}...")
                
                content["_validated_type"] = "manifest"
                if self.verbose:
                    print(f"   ✅ Manifest verified")
            else:
                if self.verbose:
                    print(f"   ⚠️  Manifest accepted without signature verification (no expected_pubkey)")
                content["_validated_type"] = "manifest (unverified)"
        
        elif "pubkey" in content:
            # Post or profile – verify signature using embedded pubkey
            if "signature" not in content:
                raise SecurityError(f"Content missing signature field")
            
            signature = content["signature"]
            pubkey_hex = content.get("pubkey")
            
            if not pubkey_hex:
                raise SecurityError(f"Content missing pubkey field")
            
            try:
                pubkey_bytes = bytes.fromhex(pubkey_hex)
            except ValueError:
                raise SecurityError(f"Invalid pubkey format: {pubkey_hex[:12]}...")
            
            if not verify_signature(content, signature, pubkey_bytes):
                raise SecurityError(f"Invalid signature for content")
            
            content["_validated_type"] = content.get("type", "post")
            if self.verbose:
                print(f"   ✅ Signature verified")
        
        else:
            # Unknown content type – accept but warn
            content["_validated_type"] = "unknown"
            if self.verbose:
                print(f"   ⚠️  Unknown content type (no pubkey, not manifest)")
        
        # Cache for future use
        if not skip_cache:
            self._save_to_cache(resolved_cid, content)
        
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
        # Don't cache metadata fields
        safe_content = {k: v for k, v in content.items() if not k.startswith("_")}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(safe_content, f, indent=2, ensure_ascii=False)
    
    def close(self):
        """Close HTTP session if open"""
        if self.session is not None:
            self.session.close()
            self.session = None
