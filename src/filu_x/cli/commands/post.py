"""Post command – create signed posts and update manifest via IPNS"""
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
from filu_x.core.id_generator import generate_post_id
from filu_x.core.resolver import LinkResolver
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.ipns import IPNSManager

def parse_reaction(content: str):
    """Parse reaction syntax: !(action)[: optional comment]"""
    pattern = r'^!\(([^)]+)\)(?::\s*(.*))?$'
    match = re.match(pattern, content.strip())
    if not match:
        return None
    
    action = match.group(1).strip()
    comment = match.group(2) or ""
    
    if action == "upvote":
        return ("vote", 1, comment)
    elif action == "downvote":
        return ("vote", -1, comment)
    elif action.startswith("react:"):
        emoji = action[6:].strip()
        if emoji:
            return ("reaction", emoji, comment)
    elif action.startswith("rate:"):
        try:
            rating = int(action[5:].strip())
            if 1 <= rating <= 5:
                return ("rating", rating, comment)
        except ValueError:
            pass
    
    raise click.UsageError(f"Unknown reaction type: {action}")

@click.command()
@click.pass_context
@click.argument("content")
@click.option("--tags", "-t", help="Tags separated by commas (e.g. python,ipfs)")
@click.option("--reply-to", help="CID of post to reply to")
@click.option("--no-thread", is_flag=True, help="Don't inherit thread participants (start new thread)")
def post(ctx, content: str, tags: str = None, reply_to: str = None, no_thread: bool = False):
    """
    Create a new post with deterministic ID.
    
    The manifest is updated and published to IPNS.
    Profile remains unchanged - followers get updates via IPNS.
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    if not layout.profile_path().exists():
        click.echo(click.style("❌ User not initialized. Run: filu-x init <username>", fg="red"))
        sys.exit(1)
    
    try:
        profile = layout.load_json(layout.profile_path())
        with open(layout.private_key_path(), "rb") as f:
            privkey_bytes = f.read()
    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error loading keys: {e}", fg="red"))
        sys.exit(1)
    
    # Parse reaction
    reaction = parse_reaction(content)
    if reaction:
        post_type, value, clean_content = reaction
        click.echo(click.style(f"📝 Creating {post_type}...", fg="cyan"))
    else:
        post_type = "text"
        value = None
        clean_content = content
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Generate deterministic ID
    post_id = generate_post_id(
        pubkey=profile["pubkey"],
        timestamp=now,
        content=clean_content
    )
    
    # Handle threading if replying
    thread_id = None
    participants = [profile["pubkey"]]
    reply_to_cid = None
    
    if reply_to and not no_thread:
        if reply_to.startswith("fx://"):
            reply_to_cid = reply_to[5:]
        else:
            reply_to_cid = reply_to
        
        try:
            click.echo(click.style(f"🔍 Fetching parent post...", fg="cyan"))
            
            ipfs = IPFSClient(mode="auto")
            resolver = LinkResolver(ipfs_client=ipfs)
            parent = resolver.resolve_content(reply_to_cid, skip_cache=False)
            
            if "thread_id" in parent and parent["thread_id"]:
                thread_id = parent["thread_id"]
            else:
                thread_id = reply_to_cid
            
            participants = parent.get("participants", [])
            
            if "pubkey" in parent and parent["pubkey"] not in participants:
                participants.append(parent["pubkey"])
            
            if profile["pubkey"] not in participants:
                participants.append(profile["pubkey"])
            
            click.echo(click.style(f"✅ Thread joined: {len(participants)} participants", fg="green"))
            
        except Exception as e:
            click.echo(click.style(f"⚠️  Could not fetch parent post: {e}", fg="yellow"))
            thread_id = None
            participants = [profile["pubkey"]]
            reply_to_cid = None
    
    # Get previous post CID for linking
    prev_post_cid = None
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
        posts = [e for e in manifest.get("entries", []) if e.get("type") in ["post", "repost", "vote", "reaction", "rating"]]
        if posts:
            prev_post_cid = posts[-1].get("cid")
    
    # Render post template
    engine = TemplateEngine()
    
    context = {
        "version": "0.0.6",
        "post_id": post_id,
        "username": profile["author"].lstrip("@"),
        "pubkey": profile["pubkey"],
        "content": clean_content,
        "prev_post_cid": prev_post_cid,
        "created_at": now,
        "updated_at": now,
        "tags": tags or "",
        "signature": ""
    }
    
    if post_type != "text":
        context["type"] = post_type
        context["value"] = value
    
    if thread_id:
        context["thread_id"] = thread_id
    if reply_to_cid:
        context["reply_to"] = reply_to_cid
    if participants:
        context["participants"] = participants
    
    post_data = engine.render_post(context)
    post_data["signature"] = sign_json(post_data, privkey_bytes)
    
    # Save post
    post_path = layout.post_path(post_id)
    layout.save_json(post_path, post_data, private=False)
    
    # ========== UPDATE MANIFEST ==========
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
    else:
        manifest = {
            "version": "0.0.6",
            "author": profile["author"],
            "root_cid": None,
            "entries": [],
            "access_points": [],
            "signature": ""
        }
    
    manifest["entries"].append({
        "path": f"posts/{post_id}.json",
        "cid": post_id,  # Will be replaced with IPFS CID during sync
        "type": post_type,
        "created_at": now,
        "priority": len(manifest["entries"]) + 1
    })
    
    click.echo(click.style(f"   📝 Manifest entries: {len(manifest['entries'])}", fg="blue"))
    
    manifest["signature"] = sign_json(manifest, privkey_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    # ======================================
    
    # ========== PUBLISH TO IPNS ==========
    ipfs = IPFSClient(mode="auto")
    ipns = IPNSManager(use_mock=True)
    
    # Add manifest to IPFS to get its CID
    manifest_cid = ipfs.add_file(layout.manifest_path())
    click.echo(click.style(f"   📦 Manifest CID in IPFS: {manifest_cid[:16]}...", fg="green"))
    
    # Publish to IPNS (updates the pointer to the new manifest)
    if profile.get("manifest_ipns"):
        ipns.publish(layout.manifest_path(), profile["manifest_ipns"])
        click.echo(click.style(f"   📌 Manifest IPNS updated to {manifest_cid[:16]}...", fg="green"))
    
    # PROFILE IS NOT UPDATED! It remains the same.
    # ======================================
    
    # Get profile CID for display (optional)
    try:
        profile_cid = ipfs.add_file(layout.profile_path())
    except:
        profile_cid = None
    
    # Success message
    if post_type == "text":
        type_str = "Post"
    elif post_type == "vote":
        type_str = "👍 Upvote" if value == 1 else "👎 Downvote"
    elif post_type == "reaction":
        type_str = f"❤️ Reaction {value}"
    elif post_type == "rating":
        type_str = f"⭐ Rating {value}/5"
    else:
        type_str = post_type.capitalize()
    
    click.echo(click.style(f"✅ {type_str} created: {post_id[:16]}...", fg="green", bold=True))
    
    preview = clean_content[:50] + "..." if len(clean_content) > 50 else clean_content
    if preview:
        click.echo(f"   Content: {preview}")
    
    if reply_to_cid:
        click.echo(f"   Reply to: {reply_to_cid[:16]}...")
    
    if thread_id:
        click.echo(f"   Thread: {thread_id[:16]}... ({len(participants)} participants)")
    
    click.echo(f"   File: {post_path}")
    
    # Show profile link
    click.echo()
    click.echo(click.style("👤 Your profile (share this to let others follow you):", fg="cyan", bold=True))
    if profile_cid:
        click.echo(f"   • fx://{profile_cid}  (direct CID)")
    if profile.get("profile_ipns"):
        click.echo(f"   • ipns://{profile['profile_ipns']}  (IPNS - never changes!)")
    click.echo()
    click.echo(click.style("💡 Followers will always see your latest posts via IPNS:", fg="blue"))
    if profile.get("manifest_ipns"):
        click.echo(f"   • ipns://{profile['manifest_ipns']}")
    
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync to IPFS:         filu-x sync")
    if reply_to_cid:
        click.echo("   • View thread:          filu-x thread show " + thread_id[:16] + "...")
