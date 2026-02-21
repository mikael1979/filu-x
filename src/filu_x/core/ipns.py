"""IPNS (InterPlanetary Naming System) management for Filu-X"""
import hashlib
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict
import click

from filu_x.core.ipfs_client import IPFSClient

class IPNSManager:
    """
    Manage IPNS names and publishing.
    
    In alpha, this uses mock implementations with a local database
    that maps each IPNS name to its own CID.
    """
    
    def __init__(self, ipfs_path: Optional[Path] = None, use_mock: bool = True):
        self.ipfs_path = ipfs_path or Path.home() / ".ipfs"
        self.use_mock = use_mock
        self.mock_db: Dict[str, str] = {}  # IPNS name -> CID
        self.mock_db_file = Path.home() / ".cache" / "filu-x" / "ipns_mock_db.json"
        self._load_mock_db()
    
    def _load_mock_db(self):
        """Load mock database from disk"""
        if self.use_mock and self.mock_db_file.exists():
            try:
                with open(self.mock_db_file, 'r') as f:
                    self.mock_db = json.load(f)
            except:
                pass
    
    def _save_mock_db(self):
        """Save mock database to disk"""
        if self.use_mock:
            self.mock_db_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.mock_db_file, 'w') as f:
                json.dump(self.mock_db, f, indent=2)
    
    def create_name(self, private_key_bytes: bytes) -> str:
        """
        Create an IPNS name from an Ed25519 private key.
        
        IPNS name is derived from the public key (peer ID).
        For alpha, we generate a deterministic mock name.
        """
        if self.use_mock:
            # Generate a deterministic mock IPNS name based on the private key
            pubkey_hash = hashlib.sha256(private_key_bytes).hexdigest()
            mock_ipns = f"k51qzi5uqu5{pubkey_hash[:40]}"
            return mock_ipns
        else:
            # Beta: actual IPNS name derivation from public key
            raise NotImplementedError("Real IPNS name generation not implemented in alpha")
    
    def publish(self, file_path: Path, ipns_name: str) -> bool:
        """
        Publish a file to IPNS.
        
        In alpha, this stores the mapping in a local database
        with the IPNS name as the key.
        """
        if self.use_mock:
            try:
                # Get CID of the file
                ipfs = IPFSClient(mode="auto")
                cid = ipfs.add_file(file_path)
                
                # Store in mock database with IPNS name as key
                self.mock_db[ipns_name] = cid
                self._save_mock_db()
                
                click.echo(click.style(
                    f"   📌 [Mock] Published {ipns_name[:16]}... -> {cid[:16]}...",
                    fg="blue"
                ))
                return True
            except Exception as e:
                click.echo(click.style(f"⚠️  Mock publish failed: {e}", fg="yellow"))
                return False
        
        # Beta: actual IPFS command
        try:
            # Get CID of the file
            result = subprocess.run(
                ["ipfs", "add", "-q", "--cid-version=1", str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            cid = result.stdout.strip()
            
            # Publish to IPNS
            subprocess.run(
                ["ipfs", "name", "publish", f"/ipfs/{cid}"],
                capture_output=True,
                check=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"⚠️  IPNS publish failed: {e}", fg="yellow"))
            return False
        except Exception as e:
            click.echo(click.style(f"⚠️  IPNS publish error: {e}", fg="yellow"))
            return False
    
    def resolve(self, ipns_name: str) -> Optional[str]:
        """
        Resolve an IPNS name to the current CID.
        
        In alpha, this looks up the local database using the exact IPNS name.
        Each IPNS name has its own CID mapping.
        """
        if self.use_mock:
            # Look up the CID for this specific IPNS name
            cid = self.mock_db.get(ipns_name)
            if cid:
                return cid
            
            # If not found, try to generate a deterministic fallback
            # This ensures that even unmapped IPNS names return something
            fallback_cid = f"bafkrei{hashlib.sha256(ipns_name.encode()).hexdigest()[:40]}"
            
            # But log a warning because this indicates a problem
            click.echo(click.style(
                f"   ⚠️  IPNS name {ipns_name[:16]}... not found in mock DB, using fallback",
                fg="yellow"
            ), err=True)
            
            return fallback_cid
        
        try:
            # Beta: actual IPFS name resolve
            result = subprocess.run(
                ["ipfs", "name", "resolve", ipns_name],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "/ipfs/<cid>"
            ipfs_path = result.stdout.strip()
            if ipfs_path.startswith("/ipfs/"):
                return ipfs_path[6:]  # Remove "/ipfs/" prefix
            return None
            
        except subprocess.CalledProcessError:
            return None
    
    def get_last_published(self, ipns_name: str) -> Optional[str]:
        """Get the last published CID for a specific IPNS name"""
        return self.mock_db.get(ipns_name)
    
    def get_name_from_pubkey(self, pubkey_bytes: bytes) -> str:
        """
        Get IPNS name (peer ID) from public key.
        
        In IPFS, the peer ID is a multihash of the public key.
        For alpha, we use a simplified version.
        """
        pubkey_hash = hashlib.sha256(pubkey_bytes).hexdigest()
        return f"12D3KooW{pubkey_hash[:40]}"
