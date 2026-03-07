"""Cryptographic operations for Filu-X using Ed25519"""
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import json
from typing import Tuple

def generate_ed25519_keypair() -> Tuple[bytes, bytes]:
    """Generate Ed25519 keypair
    
    Returns:
        Tuple of (private_key_bytes, public_key_bytes)
    """
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return (
        priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        ),
        pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    )

def sign_json(data: dict, private_key_bytes: bytes) -> str:
    """Sign JSON data with Ed25519 private key
    
    Args:
        data: Dictionary to sign (signature field will be excluded)
        private_key_bytes: Raw Ed25519 private key
    
    Returns:
        Hex-encoded signature
    """
    # Remove signature field if present before signing
    data_clean = {k: v for k, v in data.items() if k != "signature"}
    message = json.dumps(data_clean, sort_keys=True, ensure_ascii=False).encode()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    sig = priv.sign(message)
    return sig.hex()

def verify_signature(data: dict, signature_hex: str, public_key_bytes: bytes) -> bool:
    """Verify Ed25519 signature of JSON data
    
    Args:
        data: Dictionary that was signed
        signature_hex: Hex-encoded signature
        public_key_bytes: Raw Ed25519 public key
    
    Returns:
        True if signature is valid, False otherwise
    """
    data_clean = {k: v for k, v in data.items() if k != "signature"}
    message = json.dumps(data_clean, sort_keys=True, ensure_ascii=False).encode()
    pub = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        pub.verify(bytes.fromhex(signature_hex), message)
        return True
    except Exception:
        return False
