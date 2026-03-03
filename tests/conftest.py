# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path
from filu_x.core.crypto import generate_ed25519_keypair, sign_json
from filu_x.storage.layout import FiluXStorageLayout

@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_keys(temp_data_dir):
    """Generate mock Ed25519 keys for testing"""
    priv, pub = generate_ed25519_keypair()
    
    keys_dir = temp_data_dir / "user_private" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    with open(keys_dir / "ed25519_private.pem", "wb") as f:
        f.write(priv)
    with open(keys_dir / "ed25519_public.pem", "wb") as f:
        f.write(pub)
    
    return {"private": priv, "public": pub, "dir": keys_dir}

@pytest.fixture
def initialized_user(temp_data_dir):
    """Create fully initialized user for testing"""
    layout = FiluXStorageLayout(temp_data_dir)
    
    # Generate keys
    priv, pub = generate_ed25519_keypair()
    
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
        "version": "0.0.7",
        "author": "@testuser",
        "pubkey": pub.hex(),
        "profile_ipns": "k51qzi5uqu5test0000000000000000000000000000000000p",
        "manifest_ipns": "k51qzi5uqu5test0000000000000000000000000000000000m",
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
        "version": "0.0.7",
        "manifest_version": "0.0.0.0",
        "author": "@testuser",
        "root_cid": None,
        "entries": [],
        "access_points": [],
        "signature": ""
    }
    manifest["signature"] = sign_json(manifest, priv)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    # Create private config
    private_config = {
        "version": "0.0.7",
        "username": "testuser",
        "pubkey": pub.hex(),
        "encrypted": False,
        "last_used_data_dir": str(temp_data_dir),
        "default_profile_link": "fx://testcid",
        "default_profile_ipns": "",
        "recent_links": []
    }
    layout.save_json(layout.private_config_path(), private_config, private=True)
    
    # Create empty follow list
    follow_list = {
        "version": "0.0.7",
        "author": "@testuser",
        "pubkey": pub.hex(),
        "follows": [],
        "updated_at": now,
        "signature": ""
    }
    follow_list["signature"] = sign_json(follow_list, priv)
    layout.save_json(layout.follow_list_path(), follow_list, private=False)
    
    return {
        "layout": layout,
        "privkey": priv,
        "pubkey": pub,
        "data_dir": temp_data_dir
    }
