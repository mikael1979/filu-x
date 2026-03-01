"""Thread command – manage and view conversation threads with thread manifest support"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.ipns import IPNSManager


# ============================================================================
# Click group definition (MÄÄRITELLÄÄN ENNEN KOMENTOJA!)
# ============================================================================

@click.group(name="thread")
def thread():
    """Manage conversation threads"""
    pass


# ============================================================================
# Thread Manifest Class
# ============================================================================

class ThreadManifest:
    """Manage thread manifests - a special manifest containing thread metadata and posts"""
    
    def __init__(self, layout: FiluXStorageLayout, thread_id: str):
        self.layout = layout
        self.thread_id = thread_id
        self.manifest_path = layout.cached_thread_manifest_path(thread_id)
        self.public_manifest_path = layout.thread_manifest_path(thread_id, protocol="ipfs")
        self.posts_dir = self.manifest_path.parent / "posts"
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load thread manifest from disk or create default"""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                click.echo(click.style(f"⚠️  Could not load thread manifest: {e}", fg="yellow"), err=True)
        
        # Default empty thread manifest
        return {
            "thread_id": self.thread_id,
            "thread_ipns": None,
            "title": None,
            "description": None,
            "created_by": None,
            "created_at": None,
            "updated_at": None,
            "participants": [],
            "participant_count": 0,
            "post_count": 0,
            "root_post": None,
            "posts": [],  # List of post CIDs in chronological order
            "metadata": {}
        }
    
    def save(self):
        """Save thread manifest to disk"""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        # Also save to public directory for IPFS
        self.public_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.public_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def update_from_posts(self, posts: List[dict], root_post: dict = None):
        """
        Update thread manifest from list of posts.
        
        Args:
            posts: List of post dictionaries
            root_post: Root post (if None, will try to determine from posts)
        """
        if not posts:
            return
        
        # Sort posts chronologically
        posts.sort(key=lambda p: p.get("created_at", ""))
        
        # Determine root post if not provided
        if not root_post:
            # Root post has no reply_to or reply_to not in posts
            post_ids = {p.get("id") for p in posts if p.get("id")}
            for p in posts:
                reply_to = p.get("reply_to")
                if not reply_to or reply_to not in post_ids:
                    root_post = p
                    break
        
        # Update manifest data
        self.data["root_post"] = {
            "id": root_post.get("id") if root_post else None,
            "author": root_post.get("author") if root_post else None,
            "created_at": root_post.get("created_at") if root_post else None,
            "cid": root_post.get("cid") or root_post.get("id") if root_post else None
        } if root_post else None
        
        self.data["created_at"] = self.data["root_post"].get("created_at") if self.data["root_post"] else posts[0].get("created_at")
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update participants
        participants = set()
        for post in posts:
            if "pubkey" in post:
                participants.add(post["pubkey"])
            # Also add from participants list if present
            for p in post.get("participants", []):
                participants.add(p)
        
        self.data["participants"] = sorted(list(participants))
        self.data["participant_count"] = len(participants)
        
        # Update posts list (store only CIDs and basic info)
        post_list = []
        for post in posts:
            post_list.append({
                "cid": post.get("cid") or post.get("id"),
                "author": post.get("author"),
                "created_at": post.get("created_at"),
                "type": post.get("type", "post"),
                "post_type": post.get("post_type", "simple"),
                "reply_to": post.get("reply_to")
            })
        
        self.data["posts"] = post_list
        self.data["post_count"] = len(post_list)
        
        self.save()
    
    def add_post(self, post: dict):
        """Add a single post to the thread manifest"""
        # Check if post already in manifest
        post_cid = post.get("cid") or post.get("id")
        existing_cids = {p.get("cid") for p in self.data["posts"]}
        
        if post_cid in existing_cids:
            return
        
        # Add post to list
        self.data["posts"].append({
            "cid": post_cid,
            "author": post.get("author"),
            "created_at": post.get("created_at"),
            "type": post.get("type", "post"),
            "post_type": post.get("post_type", "simple"),
            "reply_to": post.get("reply_to")
        })
        
        # Re-sort posts chronologically
        self.data["posts"].sort(key=lambda p: p.get("created_at", ""))
        self.data["post_count"] = len(self.data["posts"])
        
        # Update participants if needed
        if "pubkey" in post:
            pubkey = post["pubkey"]
            if pubkey not in self.data["participants"]:
                self.data["participants"].append(pubkey)
                self.data["participants"].sort()
                self.data["participant_count"] = len(self.data["participants"])
        
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.save()
    
    def get_post_cids(self) -> List[str]:
        """Get list of all post CIDs in the thread"""
        return [p["cid"] for p in self.data["posts"]]
    
    def get_participants(self) -> List[str]:
        """Get list of all participants"""
        return self.data["participants"]
    
    def get_root_cid(self) -> Optional[str]:
        """Get root post CID"""
        if self.data["root_post"]:
            return self.data["root_post"].get("cid")
        return None
    
    def is_empty(self) -> bool:
        """Check if manifest has any posts"""
        return len(self.data["posts"]) == 0
    
    def __str__(self) -> str:
        return f"ThreadManifest(thread={self.thread_id[:16]}..., posts={self.data['post_count']}, participants={self.data['participant_count']})"


class ThreadManager:
    """Manage local thread cache and operations"""
    
    def __init__(self, layout: FiluXStorageLayout):
        self.layout = layout
        self.threads_dir = layout.cached_threads_path()
        self.threads_dir.mkdir(parents=True, exist_ok=True)
        self.resolver = LinkResolver(ipfs_client=IPFSClient(mode="auto"))
    
    def get_thread_manifest(self, thread_id: str) -> ThreadManifest:
        """Get thread manifest for a thread ID"""
        return ThreadManifest(self.layout, thread_id)
    
    def is_following(self, thread_id: str) -> bool:
        """Check if user is following this thread"""
        config = self._load_thread_config()
        return thread_id in config.get("followed_threads", [])
    
    def follow(self, thread_id: str):
        """Add thread to followed list"""
        config = self._load_thread_config()
        if "followed_threads" not in config:
            config["followed_threads"] = []
        if thread_id not in config["followed_threads"]:
            config["followed_threads"].append(thread_id)
            config["followed_threads"].sort()
            self._save_thread_config(config)
    
    def unfollow(self, thread_id: str):
        """Remove thread from followed list"""
        config = self._load_thread_config()
        if thread_id in config.get("followed_threads", []):
            config["followed_threads"].remove(thread_id)
            self._save_thread_config(config)
    
    def list_followed(self) -> list:
        """List all followed thread IDs"""
        config = self._load_thread_config()
        return config.get("followed_threads", [])
    
    def _load_thread_config(self) -> dict:
        """Load thread configuration"""
        config_path = self.layout.private_dir / "thread_config.json"
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}
    
    def _save_thread_config(self, config: dict):
        """Save thread configuration"""
        config_path = self.layout.private_dir / "thread_config.json"
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    
    def fetch_thread_posts(self, thread_id: str, root_post: dict) -> List[dict]:
        """
        Fetch all posts in a thread by discovering from participants.
        
        Returns list of posts sorted by creation time.
        """
        posts = [root_post]
        participants = root_post.get("participants", [])
        
        if not participants and "pubkey" in root_post:
            participants = [root_post["pubkey"]]
        
        click.echo(f"   📋 Fetching posts from {len(participants)} participants...")
        
        # This is a placeholder - actual implementation would need to
        # fetch each participant's manifest and look for posts with this thread_id
        
        return posts


# ============================================================================
# Helper function for rendering posts
# ============================================================================

def _render_post(post: dict, depth: int = 0, is_error: bool = False, show_cid: bool = False):
    """Render a single post with proper indentation and type indicators"""
    indent = "  " * depth
    prefix = "├─" if depth > 0 else "└─"
    
    if is_error:
        click.echo(f"{indent}{prefix} ⚠️ {post.get('content', 'Unknown error')}")
        return
    
    author = post.get("author", "unknown")
    created = post.get("created_at", "")
    content = post.get("content", "").strip()
    post_type = post.get("type", "post")
    post_cid = post.get("cid") or post.get("id", "")
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        time_str = dt.strftime("%H:%M")
    except:
        time_str = created[11:16] if len(created) > 16 else created
    
    # Choose icon based on type
    if post_type == "repost":
        icon = "🔁"
    elif post_type == "vote":
        value = post.get("value", 0)
        icon = "👍" if value == 1 else "👎"
    elif post_type == "reaction":
        icon = post.get("value", "❤️")
    elif post_type == "rating":
        stars = "⭐" * post.get("value", 0)
        icon = stars
    else:
        icon = "💬"
    
    # Render the post
    if content:
        # Truncate long content
        if len(content) > 60:
            content = content[:60] + "..."
        click.echo(f"{indent}{prefix} [{time_str}] {author} {icon} {content}")
    else:
        click.echo(f"{indent}{prefix} [{time_str}] {author} {icon}")
    
    # Optionally show post ID
    if show_cid and post_cid:
        click.echo(f"{indent}   └─ fx://{post_cid[:12]}...")


def _render_thread_manifest(manifest: ThreadManifest, verbose: bool = False):
    """Render a thread from its manifest"""
    posts = manifest.data.get("posts", [])
    
    if not posts:
        click.echo(click.style("📭 Thread has no posts", fg="yellow"))
        return
    
    # Build lookup by CID
    posts_by_cid = {p["cid"]: p for p in posts}
    
    # Find root posts (no reply_to or reply_to not in posts)
    root_posts = []
    for p in posts:
        reply_to = p.get("reply_to")
        if not reply_to or reply_to not in posts_by_cid:
            root_posts.append(p)
    
    # Sort roots chronologically
    root_posts.sort(key=lambda p: p.get("created_at", ""))
    
    # Render thread header
    root_info = manifest.data.get("root_post", {})
    root_author = root_info.get("author", "unknown") if root_info else "unknown"
    thread_title = manifest.data.get("title", "Untitled Thread")
    
    click.echo(click.style(
        f"📋 Thread: {thread_title}",
        fg="cyan",
        bold=True
    ))
    if manifest.data.get("description"):
        click.echo(click.style(f"   {manifest.data['description']}", fg="blue"))
    click.echo(click.style(
        f"   Root by: {root_author}",
        fg="blue"
    ))
    if manifest.data.get("thread_ipns"):
        click.echo(click.style(f"   IPNS: ipns://{manifest.data['thread_ipns'][:16]}...", fg="blue"))
    click.echo(click.style(
        f"   Posts: {manifest.data['post_count']}, Participants: {manifest.data['participant_count']}",
        fg="blue"
    ))
    click.echo()
    
    # Render thread tree
    def render_tree(post_cid: str, depth: int, visited: set = None):
        if visited is None:
            visited = set()
        if post_cid in visited:
            _render_post({"content": "⚠️ Cycle detected"}, depth, is_error=True)
            return
        visited.add(post_cid)
        
        post = posts_by_cid.get(post_cid)
        if not post:
            return
        
        # Convert to full post dict for rendering
        post_dict = {
            "author": post.get("author"),
            "created_at": post.get("created_at"),
            "content": post.get("content", ""),
            "type": post.get("type", "post"),
            "id": post.get("cid")
        }
        _render_post(post_dict, depth, show_cid=verbose)
        
        # Find and render replies
        replies = [p for p in posts if p.get("reply_to") == post_cid]
        replies.sort(key=lambda p: p.get("created_at", ""))
        for reply in replies:
            render_tree(reply["cid"], depth + 1, visited)
    
    # Render each root post
    for root in root_posts:
        render_tree(root["cid"], 0)


# ============================================================================
# Subcommands (nämä tulevat thread-groupin jälkeen)
# ============================================================================

@thread.command()
@click.pass_context
@click.argument("thread_id")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed post information")
@click.option("--force", "-f", is_flag=True, help="Force refresh from network")
def show(ctx, thread_id: str, verbose: bool, force: bool):
    """
    Display a complete conversation thread.
    
    Shows all posts in a thread in chronological order with proper indentation.
    Uses thread manifest for faster loading.
    
    Examples:
      filu-x thread show bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    # Clean thread ID (remove fx:// if present)
    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]
    
    # Validate CID length (basic check)
    if len(thread_id) < 10:
        click.echo(click.style(
            f"❌ Invalid CID: too short ({len(thread_id)} chars). Expected at least 10 chars.",
            fg="red"
        ))
        click.echo()
        click.echo("💡 Use a complete CID (46+ chars for IPFS CIDs)")
        sys.exit(1)
    
    click.echo(click.style(
        f"🔍 Looking up thread: {thread_id[:16]}...",
        fg="cyan"
    ))
    click.echo()
    
    # Get thread manifest
    manifest = manager.get_thread_manifest(thread_id)
    
    # If manifest is empty or force refresh, sync from network
    if manifest.is_empty() or force:
        if force:
            click.echo("   Force refresh from network...")
        else:
            click.echo("   No cached thread manifest found. Syncing from network...")
        click.echo()
        
        # Sync from network
        ctx.invoke(sync, thread_id=thread_id)
        
        # Reload manifest
        manifest = manager.get_thread_manifest(thread_id)
    
    if manifest.is_empty():
        click.echo(click.style(
            "❌ Could not fetch any posts for this thread",
            fg="red"
        ))
        click.echo()
        click.echo("💡 Tips:")
        click.echo("   • Check that the thread ID is correct")
        click.echo("   • Try 'filu-x thread sync' with the full CID")
        click.echo("   • The original posts may no longer be available")
        sys.exit(1)
    
    # Render thread from manifest
    _render_thread_manifest(manifest, verbose)
    
    # Show follow status
    if manager.is_following(thread_id):
        click.echo()
        click.echo(click.style(
            f"✅ You are following this thread",
            fg="green"
        ))


@thread.command()
@click.pass_context
@click.argument("thread_id")
@click.option("--depth", "-d", default=5, help="How deep to fetch (default: 5)")
@click.option("--force", "-f", is_flag=True, help="Force refresh even if manifest exists")
def sync(ctx, thread_id: str, depth: int, force: bool):
    """
    Fetch all posts in a thread and create/update thread manifest.
    
    Discovers posts by following reply chains from the root.
    Creates a thread manifest with all posts and metadata.
    
    Examples:
      filu-x thread sync bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]
    
    click.echo(click.style(
        f"🔄 Syncing thread: {thread_id[:16]}...",
        fg="cyan",
        bold=True
    ))
    
    # Get thread manifest
    manifest = manager.get_thread_manifest(thread_id)
    
    # If manifest exists and not force, ask user
    if not manifest.is_empty() and not force:
        click.echo(f"   📋 Thread manifest already exists with {manifest.data['post_count']} posts")
        if not click.confirm("   Sync again anyway?"):
            click.echo("   Cancelled.")
            return
    
    # Initialize resolver
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    
    # Fetch root post
    try:
        click.echo(f"   📥 Fetching root post...")
        root_post = resolver.resolve_content(thread_id, skip_cache=False)
        click.echo(click.style(f"   ✅ Root post fetched", fg="green"))
    except Exception as e:
        click.echo(click.style(f"   ❌ Failed to fetch root post: {e}", fg="red"))
        sys.exit(1)
    
    # Collect all posts in thread using BFS
    all_posts = {root_post["id"]: root_post}
    to_fetch = [root_post]
    fetched_count = 1
    
    # Get participants from root
    participants = set(root_post.get("participants", []))
    if "pubkey" in root_post:
        participants.add(root_post["pubkey"])
    
    click.echo(f"   🔍 Discovering replies (max depth: {depth})...")
    
    # BFS to find all replies
    for level in range(depth):
        next_to_fetch = []
        
        for post in to_fetch:
            # In a real implementation, we would need to:
            # 1. Get all participants' manifests
            # 2. Search for posts with thread_id = thread_id
            # 3. Also check for posts that reply_to this post
            
            # For alpha, we'll just note that this needs participants' feeds
            # This is a simplified version
            pass
        
        to_fetch = next_to_fetch
        if not to_fetch:
            break
    
    # For alpha, we'll just have the root post
    click.echo(f"   📊 Found {len(all_posts)} posts in thread")
    
    # Update manifest with all posts
    manifest.update_from_posts(list(all_posts.values()), root_post)
    
    click.echo(click.style(
        f"   ✅ Thread manifest created: {manifest.data['post_count']} posts, {manifest.data['participant_count']} participants",
        fg="green"
    ))
    
    click.echo()
    click.echo("💡 View the thread:  filu-x thread show " + thread_id[:16] + "...")


@thread.command()
@click.pass_context
@click.argument("thread_id")
def follow(ctx, thread_id: str):
    """
    Follow a thread to receive updates.
    
    Followed threads will be synced automatically with filu-x sync-threads.
    
    Examples:
      filu-x thread follow bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]
    
    manager.follow(thread_id)
    click.echo(click.style(
        f"✅ Now following thread: {thread_id[:16]}...",
        fg="green"
    ))
    
    # Suggest next steps
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo(f"   • View thread:     filu-x thread show {thread_id[:16]}...")
    click.echo(f"   • Sync updates:    filu-x sync-threads")
    click.echo(f"   • Stop following:  filu-x thread unfollow {thread_id[:16]}...")


@thread.command()
@click.pass_context
@click.argument("thread_id")
def unfollow(ctx, thread_id: str):
    """Stop following a thread"""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]
    
    manager.unfollow(thread_id)
    click.echo(click.style(
        f"✅ Stopped following thread: {thread_id[:16]}...",
        fg="green"
    ))


@thread.command()
@click.pass_context
def list(ctx):
    """List all followed threads"""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    followed = manager.list_followed()
    
    if not followed:
        click.echo(click.style(
            "📭 Not following any threads",
            fg="yellow"
        ))
        click.echo()
        click.echo("💡 Follow a thread:")
        click.echo("   filu-x thread follow <thread_id>")
        return
    
    click.echo(click.style(
        f"📋 Followed threads ({len(followed)}):",
        fg="cyan",
        bold=True
    ))
    
    for i, thread_id in enumerate(followed, 1):
        # Get thread manifest
        manifest = manager.get_thread_manifest(thread_id)
        
        post_count = manifest.data["post_count"]
        participant_count = manifest.data["participant_count"]
        thread_title = manifest.data.get("title", "Untitled")
        last_sync = manifest.data.get("updated_at", "never")
        
        if last_sync != "never":
            try:
                sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                last_sync = sync_time.strftime("%Y-%m-%d %H:%M")
            except:
                last_sync = last_sync[:16]
        
        click.echo(f"   [{i}] {thread_title[:40]}...")
        click.echo(f"       📊 {post_count} posts, {participant_count} participants, synced {last_sync}")
        click.echo(f"       ID: {thread_id[:16]}...")


@thread.command()
@click.pass_context
@click.argument("thread_id")
def refresh(ctx, thread_id: str):
    """
    Force refresh a specific thread from network.
    
    Alias for 'thread sync --force'.
    """
    ctx.invoke(sync, thread_id=thread_id, force=True)


@thread.command()
@click.pass_context
def sync_all(ctx):
    """
    Sync all followed threads.
    
    Fetches new posts from all threads you're following.
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)
    
    followed = manager.list_followed()
    
    if not followed:
        click.echo(click.style(
            "📭 Not following any threads",
            fg="yellow"
        ))
        return
    
    click.echo(click.style(
        f"🔄 Syncing {len(followed)} followed threads...",
        fg="cyan",
        bold=True
    ))
    
    for i, thread_id in enumerate(followed, 1):
        click.echo(f"\n   [{i}/{len(followed)}] Thread: {thread_id[:16]}...")
        ctx.invoke(sync, thread_id=thread_id, force=False)
    
    click.echo()
    click.echo(click.style(
        f"✅ All threads synced",
        fg="green",
        bold=True
    ))


@thread.command()
@click.pass_context
@click.argument("thread_id")
def view(ctx, thread_id: str):
    """Alias for 'thread show'"""
    ctx.invoke(show, thread_id=thread_id)


@thread.command()
@click.pass_context
@click.argument("thread_id")
def status(ctx, thread_id: str):
    """
    Show detailed status of a thread.
    
    Examples:
      filu-x thread status bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    manager = ThreadManager(layout)

    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    click.echo(click.style(f"📊 Thread Status: {thread_id[:16]}...", fg="cyan", bold=True))
    click.echo()

    # Get thread manifest
    manifest = manager.get_thread_manifest(thread_id)
    
    click.echo("📦 Thread Manifest:")
    if not manifest.is_empty():
        click.echo(f"   • Title: {manifest.data.get('title', 'Untitled')}")
        if manifest.data.get('description'):
            click.echo(f"   • Description: {manifest.data['description']}")
        click.echo(f"   • Posts: {manifest.data['post_count']}")
        click.echo(f"   • Participants: {manifest.data['participant_count']}")
        click.echo(f"   • Created: {manifest.data.get('created_at', 'unknown')}")
        click.echo(f"   • Last sync: {manifest.data.get('updated_at', 'never')}")
        
        if manifest.data.get("thread_ipns"):
            click.echo(f"   • Thread IPNS: ipns://{manifest.data['thread_ipns'][:16]}...")
        
        if manifest.data.get("root_post"):
            root = manifest.data["root_post"]
            click.echo(f"   • Root author: {root.get('author', 'unknown')}")
    else:
        click.echo("   • No cached thread manifest")

    # Check follow status
    click.echo()
    click.echo("👤 Following:")
    if manager.is_following(thread_id):
        click.echo("   • Yes (use 'thread unfollow' to stop)")
    else:
        click.echo("   • No (use 'thread follow' to start)")

    # Suggestions
    click.echo()
    click.echo("💡 Commands:")
    if manifest.is_empty():
        click.echo(f"   • Sync:    filu-x thread sync {thread_id[:16]}...")
    else:
        click.echo(f"   • View:    filu-x thread show {thread_id[:16]}...")
        click.echo(f"   • Refresh: filu-x thread refresh {thread_id[:16]}...")
    
    if not manager.is_following(thread_id):
        click.echo(f"   • Follow:  filu-x thread follow {thread_id[:16]}...")


# This is needed for the thread command group to be registered
__all__ = ['thread', 'ThreadManifest', 'ThreadManager']
