"""Post command – create signed posts with deterministic IDs and thread support"""
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

def parse_reaction(content: str):
    """
    Parse reaction syntax: !(action)[: optional comment]
    
    Returns (post_type, value, clean_content) or None if not a reaction.
    """
    pattern = r'^!\(([^)]+)\)(?::\s*(.*))?$'
    match = re.match(pattern, content.strip())
    if not match:
        return None
    
    action = match.group(1).strip()
    comment = match.group(2) or ""
    
    # Check action type
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
    
    # Unknown action
    raise click.UsageError(f"Unknown reaction type: {action}")

@click.command()
@click.pass_context
@click.argument("content")
@click.option("--tags", "-t", help="Tags separated by commas (e.g. python,ipfs)")
@click.option("--reply-to", help="CID of post to reply to")
@click.option("--no-thread", is_flag=True, help="Don't inherit thread participants (start new thread)")
def post(ctx, content: str, tags: str = None, reply_to: str = None, no_thread: bool = False):
    """
    Create a new post and save it locally with deterministic ID.
    
    Supports reactions with compact syntax:
      !(upvote): Great post!      # Upvote with comment
      !(downvote)                  # Downvote without comment
      !(react:🔥): This is hot!    # Emoji reaction
      !(rate:5): Excellent         # 5-star rating
    
    To reply to a post:
      filu-x post "My reply" --reply-to bafkrei...
    """
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
    
    # Check if this is a reaction
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
        # Clean CID (remove fx:// if present)
        if reply_to.startswith("fx://"):
            reply_to_cid = reply_to[5:]
        else:
            reply_to_cid = reply_to
        
        try:
            click.echo(click.style(f"🔍 Fetching parent post...", fg="cyan"))
            
            # Initialize resolver
            ipfs = IPFSClient(mode="auto")
            resolver = LinkResolver(ipfs_client=ipfs)
            
            # Fetch parent post
            parent = resolver.resolve_content(reply_to_cid, skip_cache=False)
            
            # Determine thread_id
            if "thread_id" in parent and parent["thread_id"]:
                thread_id = parent["thread_id"]
            else:
                thread_id = reply_to_cid  # Parent is thread root
            
            # Build participant list (copy parent's and add self)
            participants = parent.get("participants", [])
            
            # Add parent author if not already in list
            if "pubkey" in parent and parent["pubkey"] not in participants:
                participants.append(parent["pubkey"])
            
            # Add self
            if profile["pubkey"] not in participants:
                participants.append(profile["pubkey"])
            
            click.echo(click.style(
                f"✅ Thread joined: {len(participants)} participants",
                fg="green"
            ))
            
        except Exception as e:
            click.echo(click.style(
                f"⚠️  Could not fetch parent post: {e}",
                fg="yellow"
            ))
            click.echo("   Creating post without thread context.")
            thread_id = None
            participants = [profile["pubkey"]]
            reply_to_cid = None
    
    # Get previous post CID for linking (optional)
    prev_post_cid = None
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
        posts = [e for e in manifest.get("entries", []) if e.get("type") in ["post", "repost", "vote", "reaction", "rating"]]
        if posts:
            prev_post_cid = posts[-1].get("cid")
    
    # Render post template
    engine = TemplateEngine()
    
    # Build context for template
    context = {
        "version": "0.0.5",
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
    
    # Add type-specific fields
    if post_type != "text":
        context["type"] = post_type
        context["value"] = value
    
    # Add thread fields
    if thread_id:
        context["thread_id"] = thread_id
    if reply_to_cid:
        context["reply_to"] = reply_to_cid
    if participants:
        context["participants"] = participants
    
    post_data = engine.render_post(context)
    
    # Sign the post
    post_data["signature"] = sign_json(post_data, privkey_bytes)
    
    # Save post
    post_path = layout.post_path(post_id)
    layout.save_json(post_path, post_data, private=False)
    
    # Update manifest
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path())
    else:
        manifest = {
            "version": "0.0.5",
            "author": profile["author"],
            "root_cid": None,
            "entries": [],
            "access_points": [],
            "signature": ""
        }
    
    manifest["entries"].append({
        "path": f"posts/{post_id}.json",
        "cid": post_id,
        "type": post_type,
        "created_at": now,
        "priority": len(manifest["entries"]) + 1
    })
    
    manifest["signature"] = sign_json(manifest, privkey_bytes)
    layout.save_json(layout.manifest_path(), manifest, private=False)
    
    # Update profile's feed_cid
    profile["feed_cid"] = post_id
    profile["updated_at"] = now
    profile["signature"] = sign_json(profile, privkey_bytes)
    layout.save_json(layout.profile_path(), profile, private=False)
    
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
    
    click.echo(click.style(f"✅ {type_str} created: {post_id[:16]}...", fg="green"))
    
    preview = clean_content[:50] + "..." if len(clean_content) > 50 else clean_content
    if preview:
        click.echo(f"   Content: {preview}")
    
    if reply_to_cid:
        click.echo(f"   Reply to: {reply_to_cid[:16]}...")
    
    if thread_id:
        click.echo(f"   Thread: {thread_id[:16]}... ({len(participants)} participants)")
    
    click.echo(f"   File: {post_path}")
    
    # Suggest next steps
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync to IPFS:         filu-x sync")
    if reply_to_cid:
        click.echo("   • View thread:          filu-x thread show " + thread_id[:16] + "...")
