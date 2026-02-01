import sys
import getpass
from datetime import datetime
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.crypto import generate_ed25519_keypair, sign_json
from filu_x.core.templates import TemplateEngine

@click.command()
@click.argument("username")
@click.option("--no-password", is_flag=True, help="Älä kysy salasanaa (vain kehitykseen!)")
def init(username: str, no_password: bool):
    """Alusta uusi Filu-X käyttäjä"""
    layout = FiluXStorageLayout()
    
    # Salasana
    if no_password:
        password = None
        click.echo(click.style("⚠️  VAROITUS: Avain tallennetaan salaamattomana!", fg="yellow"))
    else:
        password = getpass.getpass("Salasana avaimen suojaamiseen: ")
        confirm = getpass.getpass("Vahvista salasana: ")
        if password != confirm:
            click.echo(click.style("❌ Salasanat eivät täsmää", fg="red"))
            sys.exit(1)
    
    # Avainpari
    priv_bytes, pub_bytes = generate_ed25519_keypair()
    pub_hex = pub_bytes.hex()
    
    # Tallenna julkinen avain
    with open(layout.public_key_path(), "wb") as f:
        f.write(pub_bytes)
    
    # Tallenna salainen avain (salaamaton – salaus lisätään myöhemmin)
    with open(layout.private_key_path(), "wb") as f:
        f.write(priv_bytes)
    
    # Templatit
    engine = TemplateEngine()
    now = datetime.utcnow().isoformat() + "Z"
    
    # Profiili
    profile = engine.render_profile({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_hex,
        "display_name": username,
        "bio": "",
        "now_iso8601": now,
        "signature": ""
    })
    profile["signature"] = sign_json(profile, priv_bytes)
    layout.save_json(layout.profile_path(), profile, private=False)
    
    # Manifesti
    manifest = engine.render_manifest({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_hex,
        "signature": ""
    })
    manifest["signature"] = sign_json(manifest, priv_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    # Seurantalista
    follow_list = engine.render_follow_list({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_hex,
        "now_iso8601": now,
        "signature": ""
    })
    follow_list["signature"] = sign_json(follow_list, priv_bytes)
    layout.save_json(layout.follow_list_path(), follow_list, private=False)
    
    # Yksityiset asetukset
    private_config = engine.render_private_config({
        "version": "0.0.1",
        "username": username,
        "pubkey": pub_hex,
        "encrypted": False  # Salasanasuojaus lisätään betaan
    })
    layout.save_json(layout.private_config_path(), private_config, private=True)
    
    click.echo(click.style(f"✅ Filu-X alustettu käyttäjälle @{username}", fg="green"))
    click.echo(f"   Profiili: {layout.profile_path()}")
    click.echo(f"   Julkiset tiedostot: {layout.public_dir}")
    click.echo(f"   Yksityiset tiedostot: {layout.private_dir}")
    click.echo("\nSeuraava askel: filu-x post 'Hei maailma!'")
