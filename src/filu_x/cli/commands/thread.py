"""Thread command – manage and view conversation threads"""
import sys
import json
from pathlib import Path
from datetime import datetime
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver
from filu_x.core.ipfs_client import IPFSClient


class ThreadManager:
    """Manage local thread cache and operations"""
    
    def __init__(self, layout: FiluXStorageLayout):
        self.layout = layout
        self.threads_dir = layout.base_path / "data" / "cached" / "threads"
        self.threads_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = layout.private_dir / "thread_config.json"

    def get_thread_path(self, thread_id: str) -> Path:
        """Get path to thread cache file"""
        return self.threads_dir / f"{thread_id}.json"

    def load_thread_cache(self, thread_id: str) -> dict:
        """Load cached thread data if exists"""
        path = self.get_thread_path(thread_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                # Ensure required fields
                if "posts" not in data:
                    data["posts"] = []
                if "participants" not in data:
                    data["participants"] = []
                if "last_sync" not in data:
                    data["last_sync"] = None
                return data
            except Exception as e:
                click.echo(click.style(
                    f"⚠️  Cache corrupted for thread {thread_id[:16]}...: {e}",
                    fg="yellow"
                ), err=True)
        return {"posts": [], "last_sync": None, "participants": []}

    def save_thread_cache(self, thread_id: str, data: dict):
        """Save thread data to cache"""
        path = self.get_thread_path(thread_id)
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            click.echo(f"   ✅ Thread cached to {path.name}")
        except Exception as e:
            click.echo(click.style(
                f"⚠️  Failed to save thread cache: {e}",
                fg="yellow"
            ), err=True)

    def load_config(self) -> dict:
        """Load thread configuration"""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"followed": []}

    def save_config(self, config: dict):
        """Save thread configuration"""
        try:
            self.config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        except Exception as e:
            click.echo(click.style(
                f"⚠️  Failed to save thread config: {e}",
                fg="yellow"
            ), err=True)

    def is_following(self, thread_id: str) -> bool:
        """Check if user is following this thread"""
        config = self.load_config()
        return thread_id in config.get("followed", [])

    def follow(self, thread_id: str):
        """Add thread to followed list"""
        config = self.load_config()
        if "followed" not in config:
            config["followed"] = []
        if thread_id not in config["followed"]:
            config["followed"].append(thread_id)
            config["followed"].sort()
            self.save_config(config)
            return True
        return False

    def unfollow(self, thread_id: str):
        """Remove thread from followed list"""
        config = self.load_config()
        if thread_id in config.get("followed", []):
            config["followed"].remove(thread_id)
            self.save_config(config)
            return True
        return False

    def list_followed(self) -> list:
        """List all followed thread IDs"""
        config = self.load_config()
        return config.get("followed", [])


# ============================================================================
# Click group definition
# ============================================================================

@click.group(name="thread")
def thread():
    """Manage conversation threads"""
    pass


# ============================================================================
# Helper function for rendering posts
# ============================================================================

def _render_post(post: dict, depth: int = 0):
    """Render a single post with proper indentation and type indicators"""
    indent = "  " * depth
    prefix = "├─" if depth > 0 else "└─"
    
    author = post.get("author", "unknown")
    created = post.get("created_at", "")
    content = post.get("content", "").strip()
    post_type = post.get("type", "post")
    
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
        if len(content) > 50:
            content = content[:50] + "..."
        click.echo(f"{indent}{prefix} [{time_str}] {author} {icon} {content}")
    else:
        click.echo(f"{indent}{prefix} [{time_str}] {author} {icon}")
    
    # Optionally show post ID for root posts
    if depth == 0:
        post_id = post.get("id", "")
        if post_id:
            click.echo(f"{indent}   └─ fx://{post_id[:12]}...")


# ============================================================================
# Subcommands
# ============================================================================

@thread.command()
@click.pass_context
@click.argument("thread_id")
@click.option("--depth", "-d", default=5, help="How deep to fetch (not used in alpha)")
def sync(ctx, thread_id: str, depth: int):
    """
    Fetch thread root and cache it locally.
    
    (Alpha: only root post is cached. Full thread support coming in beta.)
    
    Examples:
      filu-x thread sync bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    # Initialize
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    # Clean ID
    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    click.echo(click.style(f"🔄 Syncing thread: {thread_id[:16]}...", fg="cyan"))

    # Fetch root
    try:
        click.echo("   📥 Fetching root post...")
        root = resolver.resolve_content(thread_id, skip_cache=False)
        click.echo(click.style("   ✅ Root post fetched", fg="green"))
    except Exception as e:
        click.echo(click.style(f"   ❌ Failed: {e}", fg="red"))
        sys.exit(1)

    # Prepare cache
    posts = [root]
    participants = root.get("participants", [])
    if "pubkey" in root and root["pubkey"] not in participants:
        participants.append(root["pubkey"])

    cache = {
        "thread_id": thread_id,
        "last_sync": datetime.now().isoformat(),
        "participants": participants,
        "posts": posts
    }

    # Save
    manager.save_thread_cache(thread_id, cache)
    click.echo(click.style("   ✅ Thread cached successfully", fg="green"))
    click.echo()
    click.echo("💡 Now you can view it with: filu-x thread show " + thread_id[:16] + "...")


@thread.command()
@click.pass_context
@click.argument("thread_id")
def show(ctx, thread_id: str):
    """
    Display a cached thread.
    
    Shows all posts in a thread in chronological order with proper indentation.
    
    Examples:
      filu-x thread show bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    click.echo(click.style(f"🔍 Looking up thread: {thread_id[:16]}...", fg="cyan"))
    cache = manager.load_thread_cache(thread_id)
    posts = cache.get("posts", [])

    if not posts:
        click.echo(click.style("❌ No cached posts found.", fg="yellow"))
        click.echo()
        click.echo("💡 Sync the thread first:")
        click.echo(f"   filu-x thread sync {thread_id[:16]}...")
        return

    # Sort chronologically
    posts.sort(key=lambda p: p.get("created_at", ""))

    # Build id map
    by_id = {p["id"]: p for p in posts if "id" in p}

    # Find roots
    roots = [p for p in posts if not p.get("reply_to") or p["reply_to"] not in by_id]
    roots.sort(key=lambda p: p.get("created_at", ""))

    click.echo()
    click.echo(click.style(f"📋 Thread: {thread_id[:16]}...", fg="cyan", bold=True))
    click.echo()

    # Render tree
    def render_tree(pid, depth, visited=None):
        if visited is None:
            visited = set()
        if pid in visited:
            return
        visited.add(pid)
        post = by_id.get(pid)
        if not post:
            return
        _render_post(post, depth)
        replies = [p for p in posts if p.get("reply_to") == pid]
        replies.sort(key=lambda p: p.get("created_at", ""))
        for r in replies:
            render_tree(r["id"], depth + 1, visited)

    for root in roots:
        render_tree(root["id"], 0)

    # Stats
    participants = cache.get("participants", [])
    if not participants:
        # Collect unique participants from posts
        participant_set = set()
        for p in posts:
            if "pubkey" in p:
                participant_set.add(p["pubkey"])
        participants = list(participant_set)

    click.echo()
    click.echo(click.style("📊 Thread Statistics:", fg="cyan", bold=True))
    click.echo(f"   • Posts: {len(posts)}")
    click.echo(f"   • Participants: {len(participants)}")

    # Show follow status
    if manager.is_following(thread_id):
        click.echo()
        click.echo(click.style("✅ You are following this thread", fg="green"))


@thread.command()
@click.pass_context
@click.argument("thread_id")
def follow(ctx, thread_id: str):
    """
    Follow a thread to receive updates.
    
    Followed threads will appear in 'thread list' and can be synced with 'thread sync-all'.
    
    Examples:
      filu-x thread follow bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    if manager.follow(thread_id):
        click.echo(click.style(f"✅ Now following thread: {thread_id[:16]}...", fg="green"))
        
        # Check if thread is cached
        cache = manager.load_thread_cache(thread_id)
        if not cache.get("posts"):
            click.echo()
            click.echo("💡 This thread is not cached yet. Sync it:")
            click.echo(f"   filu-x thread sync {thread_id[:16]}...")
    else:
        click.echo(click.style(f"⚠️ Already following thread: {thread_id[:16]}...", fg="yellow"))


@thread.command()
@click.pass_context
@click.argument("thread_id")
def unfollow(ctx, thread_id: str):
    """
    Stop following a thread.
    
    Examples:
      filu-x thread unfollow bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    if manager.unfollow(thread_id):
        click.echo(click.style(f"✅ Stopped following thread: {thread_id[:16]}...", fg="green"))
    else:
        click.echo(click.style(f"⚠️ You were not following this thread", fg="yellow"))


@thread.command()
@click.pass_context
def list(ctx):
    """
    List all followed threads with their status.
    
    Shows thread ID, number of cached posts, and last sync time.
    
    Examples:
      filu-x thread list
    """
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    followed = manager.list_followed()

    if not followed:
        click.echo(click.style("📭 Not following any threads", fg="yellow"))
        click.echo()
        click.echo("💡 Follow a thread:")
        click.echo("   filu-x thread follow <thread_id>")
        return

    click.echo(click.style(f"📋 Followed threads ({len(followed)}):", fg="cyan", bold=True))
    click.echo()

    for i, thread_id in enumerate(followed, 1):
        # Get thread info from cache
        cache = manager.load_thread_cache(thread_id)
        post_count = len(cache.get("posts", []))
        last_sync = cache.get("last_sync", "never")
        
        if last_sync != "never":
            try:
                sync_time = datetime.fromisoformat(last_sync)
                last_sync = sync_time.strftime("%Y-%m-%d %H:%M")
            except:
                last_sync = last_sync[:16]
        
        # Find thread title/preview
        preview = ""
        if cache.get("posts"):
            # Get root post or first post
            root_post = next((p for p in cache["posts"] if not p.get("reply_to")), cache["posts"][0])
            content = root_post.get("content", "")[:40]
            if content:
                preview = f" - \"{content}...\""
        
        click.echo(f"   [{i}] {thread_id[:16]}...{preview}")
        click.echo(f"       📊 {post_count} posts, synced {last_sync}")
    
    click.echo()
    click.echo("💡 Commands:")
    click.echo("   • View thread:   filu-x thread show <id>")
    click.echo("   • Sync thread:   filu-x thread sync <id>")
    click.echo("   • Unfollow:      filu-x thread unfollow <id>")


@thread.command()
@click.pass_context
def sync_all(ctx):
    """
    Sync all followed threads.
    
    Fetches updates for every thread you're following.
    
    Examples:
      filu-x thread sync-all
    """
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    followed = manager.list_followed()

    if not followed:
        click.echo(click.style("📭 Not following any threads", fg="yellow"))
        return

    click.echo(click.style(f"🔄 Syncing {len(followed)} followed threads...", fg="cyan", bold=True))

    success = 0
    failed = 0

    for i, thread_id in enumerate(followed, 1):
        click.echo(f"\n   [{i}/{len(followed)}] Thread: {thread_id[:16]}...")
        try:
            # Call sync command programmatically
            ctx.invoke(sync, thread_id=thread_id)
            success += 1
        except Exception as e:
            click.echo(click.style(f"   ❌ Failed: {e}", fg="red"))
            failed += 1

    click.echo()
    if failed == 0:
        click.echo(click.style(f"✅ All {success} threads synced successfully", fg="green"))
    else:
        click.echo(click.style(f"✅ {success} threads synced, {failed} failed", fg="yellow"))


@thread.command()
@click.pass_context
@click.argument("thread_id")
def refresh(ctx, thread_id: str):
    """
    Force refresh a specific thread from network.
    
    Alias for 'thread sync'.
    
    Examples:
      filu-x thread refresh bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    ctx.invoke(sync, thread_id=thread_id)


@thread.command()
@click.pass_context
@click.argument("thread_id")
def view(ctx, thread_id: str):
    """
    Alias for 'thread show'.
    
    Examples:
      filu-x thread view bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
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
    layout = FiluXStorageLayout(base_path=ctx.obj.get("data_dir"))
    manager = ThreadManager(layout)

    if thread_id.startswith("fx://"):
        thread_id = thread_id[5:]

    click.echo(click.style(f"📊 Thread Status: {thread_id[:16]}...", fg="cyan", bold=True))
    click.echo()

    # Check cache
    cache = manager.load_thread_cache(thread_id)
    posts = cache.get("posts", [])
    
    click.echo("📦 Cache:")
    if posts:
        click.echo(f"   • Cached posts: {len(posts)}")
        click.echo(f"   • Last sync: {cache.get('last_sync', 'never')}")
    else:
        click.echo("   • Not cached")
    
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
    if not posts:
        click.echo(f"   • Sync:    filu-x thread sync {thread_id[:16]}...")
    else:
        click.echo(f"   • View:    filu-x thread show {thread_id[:16]}...")
        click.echo(f"   • Refresh: filu-x thread refresh {thread_id[:16]}...")
    
    if not manager.is_following(thread_id):
        click.echo(f"   • Follow:  filu-x thread follow {thread_id[:16]}...")
