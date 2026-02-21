"""Initialize a new Filu-X user with IPNS support (no manifest_cid)"""
import sys
import getpass
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.crypto import sign_json
from filu_x.core.templates import TemplateEngine
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.ipns import IPNSManager

@click.command()
@click.pass_context
@click.argument("username")
@click.option("--no-password", is_flag=True, help="Don't prompt for password (development only)")
def init(ctx, username: str, no_password: bool):
    """
    Initialize a new Filu-X user.
    
    Creates Ed25519 keypair, IPNS names for both profile and manifest,
    and the complete file structure. Profile contains only IPNS names,
    no direct CIDs - this ensures followers always get the latest content.
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Check if already initialized
    if layout.profile_path().exists():
        click.echo(click.style(
            f"⚠️  User already initialized at {layout.base_path}",
            fg="yellow"
        ))
        click.echo("   To reinitialize, delete the directory first:")
        click.echo(f"   rm -rf {layout.base_path}")
        sys.exit(1)
    
    # Password handling
    if no_password:
        password = None
        click.echo(click.style("⚠️  WARNING: Key stored unencrypted!", fg="yellow"))
    else:
        password = getpass.getpass("Password to encrypt key: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            click.echo(click.style("❌ Passwords do not match", fg="red"))
            sys.exit(1)
    
    # Generate keypair
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
    
    # Save public key
    with open(layout.public_key_path(), "wb") as f:
        f.write(pub_key_bytes)
    
    # Save private key (unencrypted for alpha)
    if password:
        from filu_x.core.crypto import encrypt_with_scrypt
        encrypted = encrypt_with_scrypt(priv_key_bytes, password)
        with open(layout.private_key_path(), "wb") as f:
            f.write(encrypted)
    else:
        with open(layout.private_key_path(), "wb") as f:
            f.write(priv_key_bytes)
    
    # ========== CREATE IPNS NAMES ==========
    ipns = IPNSManager(use_mock=True)  # Alpha uses mock mode
    ipfs_client = IPFSClient(mode="auto")
    
    try:
        # Create IPNS name for profile (this one followers will use)
        profile_ipns = ipns.create_name(priv_key_bytes) + "p"
        click.echo(click.style(f"   📌 Profile IPNS created: {profile_ipns[:16]}...", fg="blue"))
        
        # Create IPNS name for manifest (different from profile)
        manifest_ipns = ipns.create_name(priv_key_bytes) + "m"
        click.echo(click.style(f"   📌 Manifest IPNS created: {manifest_ipns[:16]}...", fg="blue"))
        
    except Exception as e:
        click.echo(click.style(f"⚠️  Could not create IPNS names: {e}", fg="yellow"))
        profile_ipns = ""
        manifest_ipns = ""
    # ========================================
    
    # Create templates
    engine = TemplateEngine()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Create empty manifest first with version 1
    manifest = engine.render_manifest({
        "version": "0.0.6",
        "manifest_version": 1,  # Aloitetaan versiosta 1
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "signature": ""
    })
    manifest["signature"] = sign_json(manifest, priv_key_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    # Create profile with ONLY IPNS names (no manifest_cid!)
    profile = engine.render_profile({
        "version": "0.0.6",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "profile_ipns": profile_ipns,
        "manifest_ipns": manifest_ipns,
        "signature": ""
    })
    profile["signature"] = sign_json(profile, priv_key_bytes)
    layout.save_json(layout.profile_path(), profile, private=False)
    
    # Add profile to IPFS to get its CID (for sharing)
    profile_cid = ipfs_client.add_file(layout.profile_path())
    click.echo(click.style(f"   📦 Profile CID: {profile_cid[:16]}...", fg="blue"))
    
    # ========== PUBLISH TO IPNS ==========
    # Publish profile to its IPNS name
    if profile_ipns:
        ipns.publish(layout.profile_path(), profile_ipns)
        
    # Publish manifest to its IPNS name
    if manifest_ipns:
        ipns.publish(layout.manifest_path(), manifest_ipns)
    # ======================================
    
    # Private config
    private_config = engine.render_private_config({
        "version": "0.0.6",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "encrypted": bool(password),
        "last_used_data_dir": str(layout.base_path),
        "default_profile_link": f"fx://{profile_cid}",
        "default_profile_ipns": f"ipns://{profile_ipns}" if profile_ipns else "",
        "recent_links": []
    })
    layout.save_json(layout.private_config_path(), private_config, private=True)
    
    # Empty follow list
    follow_list = engine.render_follow_list({
        "version": "0.0.6",
        "username": username,
        "pubkey": pub_key_bytes.hex(),
        "now_iso8601": now,
        "signature": ""
    })
    follow_list["signature"] = sign_json(follow_list, priv_key_bytes)
    layout.save_json(layout.follow_list_path(), follow_list, private=False)
    
    # Show success message
    click.echo(click.style(f"✅ Filu-X initialized for user @{username}", fg="green", bold=True))
    click.echo()
    click.echo(f"   Profile CID: {profile_cid}")
    click.echo(f"   Profile IPNS: {profile_ipns}" if profile_ipns else "   Profile IPNS: not available")
    click.echo(f"   Manifest IPNS: {manifest_ipns}" if manifest_ipns else "   Manifest IPNS: not available")
    click.echo(f"   Manifest version: 1")
    click.echo(f"   Data directory: {layout.base_path}")
    click.echo()
    click.echo("📋 Your profile links (share these):")
    click.echo(f"   • fx://{profile_cid}  (direct CID - changes if profile updates)")
    if profile_ipns:
        click.echo(f"   • ipns://{profile_ipns}  (IPNS - never changes!)")
    click.echo()
    click.echo("📋 Your manifest IPNS (for followers to get latest posts):")
    if manifest_ipns:
        click.echo(f"   • ipns://{manifest_ipns}  (always points to latest manifest)")
    click.echo()
    click.echo("💡 For followers to always see your updates, share the Profile IPNS link!")
    click.echo("   They will get your profile once, and then follow manifest IPNS automatically.")
    click.echo()
    click.echo("Next step: filu-x post 'Hello world!'")
