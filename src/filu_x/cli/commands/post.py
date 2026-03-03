"""Post command – create signed posts and update thread manifest with local IDs"""
import sys
import re
import json
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
from filu_x.core.id_generator import generate_post_id, generate_local_id
from filu_x.core.resolver import LinkResolver
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.ipns import IPNSManager
from filu_x.cli.commands.thread import ThreadManifest

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
@click.option("--title", "-T", help="Thread title (creates a new thread)")
@click.option("--local-id", "-l", help="Custom local ID for the post (human-friendly)")
@click.option("--description", "-d", help="Thread description (optional, only with --title)")
@click.option("--reply-to", help="CID of post to reply to (only for simple posts)")
@click.option("--tags", "-t", help="Tags separated by commas (e.g. python,ipfs)")
@click.option("--no-thread", is_flag=True, help="Don't inherit thread participants (start new thread)")
def post(ctx, content: str, title: str = None, local_id: str = None, 
         description: str = None, reply_to: str = None, tags: str = None, 
         no_thread: bool = False):
    """
    Create a new post with deterministic ID and human-friendly local ID.
    
    Local ID format: {name}.{manifest_version}_{post_hash_6chars}
    
    Examples:
      filu-x post "Hello" --title "My Discussion"
      → my-discussion.0_0_0_1_a1b2c3
      
      filu-x post "Just a test"  
      → post42.0_0_0_1_d4e5f6
      
      filu-x post "Important" --local-id announcement
      → announcement.0_0_0_1_g7h8i9
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Check if user is initialized
    if not layout.private_key_path().exists():
        click.echo(click.style("❌ User not initialized. Run: filu-x init <username>", fg="red"))
        sys.exit(1)
    
    # Load profile and private key
    try:
        profile = layout.load_json(layout.profile_path())
        with open(layout.private_key_path(), "rb") as f:
            privkey_bytes = f.read()
    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error loading keys: {e}", fg="red"))
        sys.exit(1)
    
    # Validate arguments
    if title and reply_to:
        click.echo(click.style("❌ Cannot use --title and --reply-to together", fg="red"))
        sys.exit(1)
    
    if description and not title:
        click.echo(click.style("❌ --description can only be used with --title", fg="red"))
        sys.exit(1)
    
    # Parse reaction (only for content, not for title/description)
    reaction = parse_reaction(content)
    if reaction:
        post_type_value, value, clean_content = reaction
        click.echo(click.style(f"📝 Creating {post_type_value}...", fg="cyan"))
    else:
        post_type_value = None
        value = None
        clean_content = content
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Generate deterministic ID (hash-based)
    post_id = generate_post_id(
        pubkey=profile["pubkey"],
        timestamp=now,
        content=clean_content
    )
    
    # Initialize IPFS and IPNS
    ipfs = IPFSClient(mode="auto")
    ipns = IPNSManager(use_mock=True)
    
    # ========== THREAD HANDLING ==========
    post_type = "simple"
    thread_id = None
    thread_ipns = None
    participants = [profile["pubkey"]]
    reply_to_cid = None
    root_post_data = None
    
    # Load or create manifest to get version and post count
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path(protocol="ipfs"))
        manifest_version = manifest.get("manifest_version", "0.0.0.0")
        post_number = len(manifest.get("entries", [])) + 1
    else:
        manifest_version = "0.0.0.0"
        post_number = 1
    
    # Generate local ID with manifest version and post hash
    if title:
        # Use title for thread posts
        final_local_id = generate_local_id(post_id, manifest_version, custom_name=title)
    elif local_id:
        # Use custom local ID
        final_local_id = generate_local_id(post_id, manifest_version, custom_name=local_id)
    else:
        # Auto-generate with post number
        final_local_id = generate_local_id(post_id, manifest_version, post_number=post_number)
    
    if title:
        post_type = "thread"
        thread_id = post_id  # Thread ID is the root post ID
        
        # Create IPNS name for the thread
        thread_ipns = ipns.create_name(privkey_bytes) + f"t{post_id[:8]}"
        layout.save_thread_ipns(thread_id, thread_ipns)
        
        click.echo(click.style(f"📌 New thread IPNS: {thread_ipns[:16]}...", fg="blue"))
        
        # Create thread manifest
        thread_manifest = ThreadManifest(layout, thread_id)
        
        # Create initial thread manifest data
        thread_manifest.data = {
            "thread_id": thread_id,
            "thread_ipns": thread_ipns,
            "title": title,
            "description": description or "",
            "created_by": profile["author"],
            "created_at": now,
            "updated_at": now,
            "participants": [profile["pubkey"]],
            "participant_count": 1,
            "post_count": 0,
            "root_post": None,
            "posts": []
        }
        thread_manifest.save()
        
        click.echo(click.style(f"📋 Thread manifest created", fg="green"))
    
    elif reply_to and not no_thread:
        post_type = "simple"
        
        # Clean CID
        if reply_to.startswith("fx://"):
            reply_to_cid = reply_to[5:]
        else:
            reply_to_cid = reply_to
        
        try:
            click.echo(click.style(f"🔍 Fetching parent post...", fg="cyan"))
            
            # First try to find parent post locally
            parent_path = layout.post_path(reply_to_cid, protocol="ipfs")
            parent = None
            
            if parent_path.exists():
                parent = layout.load_json(parent_path)
                click.echo(click.style(f"✅ Found parent locally", fg="green"))
            else:
                # Try to resolve from IPFS
                resolver = LinkResolver(ipfs_client=ipfs)
                parent = resolver.resolve_content(reply_to_cid, skip_cache=False)
                click.echo(click.style(f"✅ Found parent from IPFS", fg="green"))
            
            # Determine thread_id
            if parent.get("post_type") == "thread":
                # Parent is a thread root
                thread_id = parent["id"]
                thread_ipns = parent.get("thread_ipns")
            else:
                # Parent is a reply in a thread
                thread_id = parent.get("thread_id")
                thread_ipns = parent.get("thread_ipns")
            
            if not thread_id:
                thread_id = reply_to_cid
            
            # Build participant list
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
            
            # If this is a reply, try to get root post for thread manifest
            if thread_id:
                try:
                    # Try to fetch root post (if different from parent)
                    if thread_id != reply_to_cid:
                        root_post_data = resolver.resolve_content(thread_id, skip_cache=False)
                    else:
                        root_post_data = parent
                except:
                    # Root post might not be available locally
                    pass
            
        except Exception as e:
            click.echo(click.style(
                f"⚠️  Could not fetch parent post: {e}",
                fg="yellow"
            ))
            click.echo("   Creating post without thread context.")
            thread_id = None
            participants = [profile["pubkey"]]
            reply_to_cid = None
    
    else:
        post_type = "simple"
        thread_id = None
        participants = [profile["pubkey"]]
    
    # Get previous post CID for linking (optional)
    prev_post_cid = None
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path(protocol="ipfs"))
        posts = [e for e in manifest.get("entries", []) if e.get("type") in ["post", "repost", "vote", "reaction", "rating"]]
        if posts:
            prev_post_cid = posts[-1].get("cid")
    
    # Render post template
    engine = TemplateEngine()
    
    # Build context for template
    context = {
        "version": "0.0.8",
        "post_id": post_id,
        "local_id": final_local_id,
        "username": profile["author"].lstrip("@"),
        "pubkey": profile["pubkey"],
        "post_type": post_type,
        "content": clean_content,
        "prev_post_cid": prev_post_cid,
        "created_at": now,
        "updated_at": now,
        "tags": tags or "",
        "signature": ""
    }
    
    # Add reaction type if needed
    if post_type_value:
        context["type"] = post_type_value
        context["value"] = value
    
    # Add thread fields
    if post_type == "thread":
        context["thread_title"] = title
        context["thread_description"] = description or ""
        context["thread_ipns"] = thread_ipns
        context["thread_id"] = thread_id
    else:
        # Simple post may have thread context
        if thread_id:
            context["thread_id"] = thread_id
            context["thread_ipns"] = thread_ipns
        if reply_to_cid:
            context["reply_to"] = reply_to_cid
        if participants:
            context["participants"] = participants
    
    # Render and sign
    post_data = engine.render_post(context)
    post_data["signature"] = sign_json(post_data, privkey_bytes)
    
    # Save post to IPFS public directory
    post_path = layout.post_path(post_id, protocol="ipfs")
    layout.save_json(post_path, post_data, private=False)
    
    # Also save to local directory with friendly name
    local_posts_dir = layout.base_path / "local" / "posts"
    local_posts_dir.mkdir(parents=True, exist_ok=True)
    local_post_path = local_posts_dir / final_local_id
    layout.save_json(local_post_path, post_data, private=False)
    
    # Update local mapping file
    mapping_file = layout.base_path / "local" / "mapping.json"
    mapping = {}
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
    
    mapping[final_local_id] = {
        "post_id": post_id,
        "manifest_version": manifest_version,
        "created_at": now,
        "path": str(local_post_path),
        "post_type": post_type,
        "title": title if title else None
    }
    
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    # ========== UPDATE MANIFEST ==========
    if layout.manifest_path().exists():
        manifest = layout.load_json(layout.manifest_path(protocol="ipfs"))
    else:
        manifest = {
            "version": "0.0.8",
            "author": profile["author"],
            "root_cid": None,
            "entries": [],
            "access_points": [],
            "signature": ""
        }
    
    manifest["entries"].append({
        "path": f"posts/{post_id}.json",
        "cid": post_id,
        "local_id": final_local_id,
        "type": post_type_value or "text",
        "post_type": post_type,
        "created_at": now,
        "priority": len(manifest["entries"]) + 1
    })
    
    click.echo(click.style(f"   📝 Manifest entries: {len(manifest['entries'])}", fg="blue"))
    
    manifest["signature"] = sign_json(manifest, privkey_bytes)
    layout.save_json(layout.manifest_path(protocol="ipfs"), manifest, private=False)
    # ======================================
    
    # ========== UPDATE THREAD MANIFEST ==========
    if thread_id and post_type == "simple":
        try:
            thread_manifest = ThreadManifest(layout, thread_id)
            
            # Add this post to thread manifest
            thread_manifest.add_post(post_data)
            
            click.echo(click.style(f"   📋 Thread manifest updated: {thread_manifest.data['post_count']} posts", fg="green"))
            
        except Exception as e:
            click.echo(click.style(f"   ⚠️  Could not update thread manifest: {e}", fg="yellow"))
    # ============================================
    
    # ========== PUBLISH TO IPFS ==========
    # Add manifest to IPFS to get its CID
    manifest_cid = ipfs.add_file(layout.manifest_path(protocol="ipfs"))
    click.echo(click.style(f"   📦 Manifest CID in IPFS: {manifest_cid[:16]}...", fg="green"))
    
    # Update manifest version in local mapping (version might have changed)
    new_manifest_version = manifest.get("manifest_version", manifest_version)
    if new_manifest_version != manifest_version:
        # Update mapping with new version
        mapping[final_local_id]["manifest_version"] = new_manifest_version
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
    
    # Publish to IPNS (updates the pointer to the new manifest)
    if profile.get("manifest_ipns"):
        ipns.publish(layout.manifest_path(protocol="ipfs"), profile["manifest_ipns"])
        click.echo(click.style(f"   📌 Manifest IPNS updated to {manifest_cid[:16]}...", fg="green"))
    
    # If this is a new thread, publish thread manifest to its IPNS
    if post_type == "thread" and thread_ipns:
        thread_manifest_path = layout.thread_manifest_path(thread_id, protocol="ipfs")
        thread_manifest_cid = ipfs.add_file(thread_manifest_path)
        ipns.publish(thread_manifest_path, thread_ipns)
        click.echo(click.style(f"   📌 Thread IPNS updated to {thread_manifest_cid[:16]}...", fg="green"))
    # ======================================
    
    # Get profile CID for display (optional)
    try:
        profile_cid = ipfs.add_file(layout.profile_path(protocol="ipfs"))
    except:
        profile_cid = None
    
    # Success message
    if post_type == "thread":
        type_str = "Thread"
        emoji = "📌"
    elif post_type_value == "vote":
        type_str = "👍 Upvote" if value == 1 else "👎 Downvote"
        emoji = "👍" if value == 1 else "👎"
    elif post_type_value == "reaction":
        type_str = f"❤️ Reaction {value}"
        emoji = "❤️"
    elif post_type_value == "rating":
        type_str = f"⭐ Rating {value}/5"
        emoji = "⭐"
    else:
        type_str = "Post"
        emoji = "📝"
    
    click.echo(click.style(f"✅ {emoji} {type_str} created: {final_local_id}", fg="green", bold=True))
    click.echo(f"   ID: {post_id[:16]}...")
    click.echo(f"   Local ID: {final_local_id}")
    click.echo(f"   Manifest version: {new_manifest_version}")
    
    preview = clean_content[:50] + "..." if len(clean_content) > 50 else clean_content
    if preview:
        click.echo(f"   Content: {preview}")
    
    if post_type == "thread":
        click.echo(f"   Title: {title}")
        if description:
            click.echo(f"   Description: {description}")
        click.echo(f"   Thread IPNS: ipns://{thread_ipns}")
    elif reply_to_cid:
        click.echo(f"   Reply to: {reply_to_cid[:16]}...")
    
    if thread_id and post_type == "simple":
        click.echo(f"   Thread: {thread_id[:16]}... ({len(participants)} participants)")
    
    click.echo(f"   File: {post_path}")
    click.echo(f"   Local copy: {local_post_path}")
    
    # Show profile link
    click.echo()
    click.echo(click.style("👤 Your profile (share this to let others follow you):", fg="cyan", bold=True))
    if profile_cid:
        click.echo(f"   • fx://{profile_cid}  (direct CID)")
    if profile.get("profile_ipns"):
        click.echo(f"   • ipns://{profile['profile_ipns']}  (IPNS - never changes!)")
    
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync to IPFS:         filu-x sync")
    if post_type == "thread":
        click.echo("   • View thread:          filu-x thread show " + thread_id[:16] + "...")
    elif reply_to_cid:
        click.echo("   • View thread:          filu-x thread show " + thread_id[:16] + "...")
    click.echo("   • Use local ID:          filu-x local show " + final_local_id)
