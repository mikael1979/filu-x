# src/filu_x/cli/commands/init.py
import sys
from pathlib import Path
import getpass
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.crypto import generate_ed25519_keypair, sign_json
from filu_x.core.templates import TemplateEngine
import click

@click.command()
@click.argument("username")
@click.option("--no-password", is_flag=True, help="Don't prompt for password (development only)")
def init(username: str, no_password: bool):
    """Initialize a new Filu-X user"""
    layout = FiluXStorageLayout()
    
    # 1. Ask for password (if not in dev mode)
    if no_password:
        password = None
        click.echo(click.style("⚠️  WARNING: Key stored unencrypted!", fg="yellow"))
    else:
        password = getpass.getpass("Password to encrypt key: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            click.echo(click.style("❌ Passwords do not match", fg="red"))
            sys.exit(1)
    
    # 2. Generate keypair
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    
    pub_key_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    priv_key_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 3. Save public key
    with open(layout.public_key_path(), "wb") as f:
        f.write(pub_key_bytes)
    
    # 4. Save private key (unencrypted for alpha)
    if password:
        from filu_x.core.crypto import encrypt_with_scrypt
        encrypted = encrypt_with_scrypt(priv_key_bytes, password)
        with open(layout.private_key_path(), "wb") as f:
            f.write(encrypted)
    else:
        with open(layout.private_key_path(), "wb") as f:
            f.write(priv_key_bytes)
    
    # 5. Create templates
    engine = TemplateEngine()
    now = "2026-02-14T00:00:00Z"  # TODO: datetime.now().isoformat()
    
    # Profile (without signature first – sign then)
    profile = engine.render_profile({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "signature": ""
    })
    
    # Sign profile
    profile["signature"] = sign_json(profile, priv_key_bytes)
    
    # Save
    layout.save_json(layout.profile_path(), profile, private=False)
    
    # Manifest
    manifest = engine.render_manifest({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "signature": ""
    })
    manifest["signature"] = sign_json(manifest, priv_key_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    # Private config
    private_config = engine.render_private_config({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "encrypted": bool(password)
    })
    layout.save_json(layout.private_config_path(), private_config, private=True)
    
    # Empty follow list
    follow_list = engine.render_follow_list({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "signature": ""
    })
    follow_list["signature"] = sign_json(follow_list, priv_key_bytes)
    layout.save_json(layout.follow_list_path(), follow_list, private=False)
    
    click.echo(click.style(f"✅ Filu-X initialized for user @{username}", fg="green"))
    click.echo(f"   Profile: {layout.profile_path()}")
    click.echo(f"   Public files: {layout.public_dir}")
    click.echo(f"   Private files: {layout.private_dir}")
    click.echo()
    click.echo("Next step: filu-x post 'Hello world!'")
