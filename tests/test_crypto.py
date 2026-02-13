from filu_x.core.crypto import generate_ed25519_keypair, sign_json, verify_signature

def test_sign_and_verify():
    priv, pub = generate_ed25519_keypair()
    data = {"message": "hello", "timestamp": "2025-01-01T00:00:00Z"}
    sig = sign_json(data, priv)
    assert verify_signature(data, sig, pub)
