"""Link generator for Filu-X content"""
from urllib.parse import urlencode, quote
from typing import Optional
from filu_x.core.ipfs_mock import MockIPFSClient

class LinkGenerator:
    """Generates fx:// links for Filu-X content"""
    
    PROTOCOL = "fx"
    
    def __init__(self, ipfs_client: Optional[MockIPFSClient] = None):
        self.ipfs = ipfs_client or MockIPFSClient()
    
    def generate_profile_link(self, profile_cid: str, pubkey: str) -> str:
        """Generate link to user profile"""
        params = {
            "author": self._short_pubkey(pubkey),
            "type": "profile"
        }
        return self._build_link(profile_cid, params)
    
    def generate_post_link(self, post_cid: str, pubkey: str) -> str:
        """Generate link to post"""
        params = {
            "author": self._short_pubkey(pubkey),
            "type": "post"
        }
        return self._build_link(post_cid, params)
    
    def generate_latest_link(self, layout) -> str:
        """Generate link to latest post from user's data"""
        # Load profile to get pubkey
        profile = layout.load_json(layout.profile_path())
        pubkey = profile["pubkey"]
        
        # Get latest post CID from manifest
        manifest = layout.load_json(layout.manifest_path())
        posts = [e for e in manifest.get("entries", []) if e.get("type") == "post"]
        
        if not posts:
            raise ValueError("No posts found. Create a post first with 'filu-x post'")
        
        latest_cid = posts[-1]["cid"]
        return self.generate_post_link(latest_cid, pubkey)
    
    def _build_link(self, cid: str, params: dict) -> str:
        """Build fx:// link with query parameters"""
        query = urlencode(params)
        return f"{self.PROTOCOL}://{cid}?{query}"
    
    def _short_pubkey(self, pubkey: str) -> str:
        """Shorten pubkey for URL (first 8 chars after prefix)"""
        if pubkey.startswith("ed25519:"):
            return f"ed25519:{pubkey[8:12]}"
        return pubkey[:8]
    
    def parse_link(self, link: str) -> dict:
        """
        Parse fx:// link into components.
        Returns dict with keys: protocol, cid, author, type
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
        
        # Parse query parameters
        params = {}
        if query_part:
            for pair in query_part.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    params[key] = value
        
        return {
            "protocol": self.PROTOCOL,
            "cid": cid,
            "author": params.get("author", ""),
            "type": params.get("type", "unknown")
        }
