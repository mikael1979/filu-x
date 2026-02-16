"""Post command – create signed posts"""
import sys
import re
from datetime import datetime, timezone
import click
try:
    from slugify import slugify
except ImportError:
    def slugify(text, **kwargs):
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        return text[:30]

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.crypto import sign_json
from filu_x.core.templates import TemplateEngine

def generate_post_id(content: str, timestamp: datetime) -> str:
    slug = slugify(content[:30], max_length=20)
    if not slug or slug == "-":
        slug = "post"
    return f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{slug}"

@click.command()
@click.pass_context
@click.argument("content")
@click.option("--tags", "-t", help="Tags separated by commas (e.g. python,ipfs)")
def post(ctx, content: str, tags: str = None):
    """Create a new post and save it locally"""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run first: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    try:
        profile = layout.load_json(layout.profile_path())
        with open(layout.private_key_path(), "rb") as f:
            privkey_bytes = f.read()
    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error loading keys: {e}", fg="red"))
        sys.exit(1)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    post_id = generate_post_id(content, datetime.now())
    
    prev_post_cid = None
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
        posts = [e for e in manifest.get("entries", []) if e.get("type") == "post"]
        if posts:
            prev_post_cid = posts[-1].get("cid")
    
    engine = TemplateEngine()
    post_data = engine.render_post({
        "version": "0.0.1",
        "post_id": post_id,
        "username": profile["author"].lstrip("@"),
        "pubkey": profile["pubkey"],
        "content": content,
        "prev_post_cid": prev_post_cid,
        "created_at": now,
        "updated_at": now,
        "tags": tags or "",
        "signature": ""
    })
    
    post_data["signature"] = sign_json(post_data, privkey_bytes)
    post_path = layout.post_path(post_id)
    layout.save_json(post_path, post_data, private=False)
    
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
    else:
        manifest = {
            "version": "0.0.1",
            "author": profile["author"],
            "root_cid": None,
            "entries": [],
            "access_points": [],
            "signature": ""
        }
    
    manifest["entries"].append({
        "path": f"posts/{post_id}.json",
        "cid": post_id,
        "type": "post",
        "priority": len(manifest["entries"]) + 1
    })
    
    manifest["signature"] = sign_json(manifest, privkey_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    profile["feed_cid"] = post_id
    profile["updated_at"] = now
    profile["signature"] = sign_json(profile, privkey_bytes)
    layout.save_json(layout.profile_path(), profile, private=False)
    
    click.echo(click.style(f"✅ Post created: {post_id}", fg="green"))
    preview = content[:50] + "..." if len(content) > 50 else content
    click.echo(f"   Content: {preview}")
    click.echo(f"   File: {post_path}")
    click.echo(f"   Pubkey: {profile['pubkey'][:12]}...")
