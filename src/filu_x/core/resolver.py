"""Resolve and verify Filu-X content from fx:// links"""
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
from urllib.parse import urlparse, parse_qs

from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import verify_signature
from filu_x.core.content_validator import ContentValidator

# Määrittele poikkeukset ENSIN ennen kuin niitä käytetään
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
        self.validator = ContentValidator()
    
    def parse_fx_link(self, link: str) -> Dict[str, str]:
        """
        Parse fx:// link into components.
        
        Examples:
          fx://bafkrei... 
          fx://bafkrei...?author=ed25519:8a1b&type=post
        """
        if not link.startswith(f"{self.PROTOCOL}://"):
            raise ValueError(f"Invalid protocol. Expected '{self.PROTOCOL}://' prefix")
        
        # Remove protocol prefix
        rest = link[len(f"{self.PROTOCOL}://"):]
        
        # Split CID and query
        if "?" in rest:
            cid_part, query_part = rest.split("?", 1)
        else:
            cid_part, query_part = rest, ""
        
        cid = cid_part.strip()
        
        # Validate CID format (CIDv0: Qm..., CIDv1: base32 multibase)
        if not re.match(r'^[a-zA-Z0-9]{46,}$', cid):
            raise ValueError(f"Invalid CID format: {cid}")
        
        # Parse query parameters
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
        Returns verified content dict or raises ResolutionError.
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
        
        # 4. Verify signature (critical security step)
        if "signature" not in content:
            raise SecurityError(f"Content missing signature field")
        
        signature = content["signature"]
        pubkey_hex = content.get("pubkey")
        
        if not pubkey_hex:
            raise SecurityError(f"Content missing pubkey field")
        
        try:
            pubkey_bytes = bytes.fromhex(pubkey_hex)
        except ValueError:
            raise SecurityError(f"Invalid pubkey format")
        
        # Verify signature covers entire content (excluding signature field itself)
        if not verify_signature(content, signature, pubkey_bytes):
            raise SecurityError(f"Invalid signature for CID: {cid}")
        
        # 5. Validate content type
        content_type = content.get("content_type", "text/plain")
        try:
            # Simple validation - in real implementation use ContentValidator
            if content_type not in [
                "text/plain", "text/markdown", "application/json",
                "image/png", "image/jpeg", "image/gif", "image/webp",
                "video/mp4", "audio/mpeg"
            ]:
                raise SecurityError(f"Blocked unsafe content type: {content_type}")
            content["_validated_type"] = content_type
        except SecurityError as e:
            raise SecurityError(f"Blocked unsafe content: {e}")
        
        # 6. Cache for future use
        if not skip_cache:
            self._save_to_cache(cid, content)
        
        return content
    
    def render_content(self, content: Dict[str, Any], raw: bool = False) -> str:
        """
        Render content safely for display.
        Returns formatted string ready for terminal output.
        """
        content_type = content.get("_validated_type", "text/plain")
        raw_content = content.get("content", "")
        
        if raw:
            # Return raw JSON for debugging
            return json.dumps(content, indent=2, ensure_ascii=False)
        
        # Safe rendering based on content type
        if content_type == "text/plain":
            return self._render_plain(raw_content)
        
        elif content_type == "text/markdown":
            return self._render_markdown(raw_content)
        
        elif content_type == "application/json":
            return self._render_json(raw_content)
        
        elif content_type.startswith("image/") or content_type.startswith("video/") or content_type.startswith("audio/"):
            return self._render_media(content_type, content.get("cid", content.get("id", "")))
        
        else:
            # Fallback: show type and truncated content
            preview = raw_content[:100] + "..." if len(raw_content) > 100 else raw_content
            return f"[{content_type}]\n{preview}"
    
    def _render_plain(self, text: str) -> str:
        return text.strip()
    
    def _render_markdown(self, md: str) -> str:
        # For terminal: convert to plain text with minimal formatting
        return md.strip()
    
    def _render_html(self, html: str) -> str:
        # Simple tag stripping for terminal
        import re
        text = re.sub(r'<[^>]+>', '', html)
        return text.strip()
    
    def _render_json(self, content: str) -> str:
        try:
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except:
            return content[:200] + "..." if len(content) > 200 else content
    
    def _render_media(self, mime_type: str, cid: str) -> str:
        gateway_url = self.ipfs.get_gateway_url(cid)
        return f"[{mime_type}] View at: {gateway_url}"
    
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
        # Remove signature from cached copy to avoid confusion
        safe_content = {k: v for k, v in content.items() if k != "signature"}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(safe_content, f, indent=2, ensure_ascii=False)
