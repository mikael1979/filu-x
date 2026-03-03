"""Pytest fixtures for Filu-X testing"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from click.testing import CliRunner
from filu_x.core.crypto import generate_ed25519_keypair, sign_json
from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.ipns import IPNSManager

# ============================================================================
# Perus fixturet
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def runner():
    """Click CLI test runner"""
    return CliRunner()

@pytest.fixture
def data_dir(temp_dir):
    """Create data directory structure"""
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def layout(data_dir):
    """Create storage layout instance"""
    return FiluXStorageLayout(data_dir)

@pytest.fixture
def keypair():
    """Generate Ed25519 keypair"""
    priv, pub = generate_ed25519_keypair()
    return {"private": priv, "public": pub}

# ============================================================================
# Mock IPFS ja IPNS
# ============================================================================

@pytest.fixture
def mock_ipfs():
    """Mock IPFS client for testing"""
    class MockIPFS:
        def __init__(self):
            self.files = {}
            self.pins = set()
        
        def add_file(self, path):
            import hashlib
            with open(path, "rb") as f:
                content = f.read()
            cid = hashlib.sha256(content).hexdigest()[:32]
            self.files[cid] = content
            return cid
        
        def cat(self, cid):
            return self.files.get(cid)
        
        def pin_add(self, cid):
            self.pins.add(cid)
            return True
    
    return MockIPFS()

@pytest.fixture
def mock_ipns():
    """Mock IPNS manager for testing"""
    class MockIPNS:
        def __init__(self):
            self.published = {}
        
        def publish(self, path, name):
            import hashlib
            with open(path, "rb") as f:
                content = f.read()
            cid = hashlib.sha256(content).hexdigest()[:32]
            self.published[name] = cid
            return True
        
        def resolve(self, name):
            return self.published.get(name)
    
    return MockIPNS()

# ============================================================================
# Käyttäjäfixturet
# ============================================================================

@pytest.fixture
def user(layout, keypair):
    """Create initialized user"""
    priv, pub = keypair["private"], keypair["public"]
    
    # Save keys
    keys_dir = layout.private_dir / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    with open(layout.private_key_path(), "wb") as f:
        f.write(priv)
    with open(layout.public_key_path(), "wb") as f:
        f.write(pub)
    
    # Create profile
    now = "2024-01-01T00:00:00Z"
    profile = {
        "version": "0.0.8",
        "author": "@testuser",
        "pubkey": pub.hex(),
        "profile_ipns": "k51qzi5uqu5testp",
        "manifest_ipns": "k51qzi5uqu5testm",
        "threads_ipns": {},
        "bio": "",
        "avatar_url": "",
        "created_at": now,
        "updated_at": now,
        "access_points": [],
        "signature": ""
    }
    profile["signature"] = sign_json(profile, priv)
    layout.save_json(layout.profile_path(), profile, private=False)
    
    # Create empty manifest
    manifest = {
        "version": "0.0.8",
        "manifest_version": "0.0.0.0",
        "author": "@testuser",
        "pubkey": pub.hex(),
        "root_cid": None,
        "entries": [],
        "access_points": {},
        "created_at": now,
        "updated_at": now,
        "signature": ""
    }
    manifest["signature"] = sign_json(manifest, priv)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    return {
        "layout": layout,
        "privkey": priv,
        "pubkey": pub,
        "profile": profile,
        "manifest": manifest,
        "data_dir": layout.base_path
    }

@pytest.fixture
def alice(user):
    """Alias for first user"""
    return user

@pytest.fixture
def bob(data_dir):
    """Create second user for follow tests"""
    bob_layout = FiluXStorageLayout(data_dir / "bob")
    priv, pub = generate_ed25519_keypair()
    
    # Save keys
    keys_dir = bob_layout.private_dir / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    with open(bob_layout.private_key_path(), "wb") as f:
        f.write(priv)
    with open(bob_layout.public_key_path(), "wb") as f:
        f.write(pub)
    
    # Create profile
    now = "2024-01-01T00:00:00Z"
    profile = {
        "version": "0.0.8",
        "author": "@bob",
        "pubkey": pub.hex(),
        "profile_ipns": "k51qzi5uqu5bobp",
        "manifest_ipns": "k51qzi5uqu5bobm",
        "threads_ipns": {},
        "bio": "",
        "avatar_url": "",
        "created_at": now,
        "updated_at": now,
        "access_points": [],
        "signature": ""
    }
    profile["signature"] = sign_json(profile, priv)
    bob_layout.save_json(bob_layout.profile_path(), profile, private=False)
    
    return {
        "layout": bob_layout,
        "privkey": priv,
        "pubkey": pub,
        "profile": profile,
        "data_dir": bob_layout.base_path
    }

# ============================================================================
# Testidata fixturet
# ============================================================================

@pytest.fixture
def sample_post():
    """Sample post data"""
    return {
        "version": "0.0.8",
        "id": "a1b2c3d4e5f678901234567890abcdef",
        "local_id": "test-post.0_0_0_0_a1b2c3",
        "author": "@testuser",
        "pubkey": "a" * 64,
        "content": "This is a test post",
        "protocols": {
            "ipfs": {
                "cid": None,
                "gateway": "https://ipfs.io/ipfs/",
                "ipns": {
                    "name": None,
                    "gateway": "https://ipfs.io/ipns/",
                    "sequence": 0,
                    "previous": None
                }
            },
            "http": {
                "primary": None,
                "mirrors": [],
                "last_checked": None
            },
            "nostr": {
                "event_id": None,
                "relay": None,
                "kind": 1,
                "tags": []
            }
        },
        "created_at": "2024-01-01T00:00:00Z",
        "signature": "a" * 128
    }

@pytest.fixture
def sample_thread_post():
    """Sample thread post data"""
    return {
        "version": "0.0.8",
        "id": "thread1234567890abcdef1234567890ab",
        "local_id": "test-thread.0_0_0_0_thread1",
        "author": "@testuser",
        "pubkey": "a" * 64,
        "content": "Thread root",
        "post_type": "thread",
        "thread_title": "Test Thread",
        "thread_description": "This is a test thread",
        "protocols": {
            "ipfs": {
                "cid": None,
                "gateway": "https://ipfs.io/ipfs/",
                "ipns": {
                    "name": "k51qzi5uqu5thread",
                    "gateway": "https://ipfs.io/ipns/",
                    "sequence": 1,
                    "previous": None
                }
            },
            "http": {
                "primary": None,
                "mirrors": [],
                "last_checked": None
            }
        },
        "created_at": "2024-01-01T00:00:00Z",
        "signature": "a" * 128
    }
