Tässä on päivitetty `README.md` versiolle 0.0.5 Alpha "Social Alpha":

```markdown
# Filu-X

> Files as social media. Own your data. Verify everything.  
> **Unix philosophy: Everything is a file.**

[![Alpha](https://img.shields.io/badge/version-0.0.5-alpha?color=orange)](https://github.com/mikael1979/filu-x/releases)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

Filu-X is a file-based approach to decentralized social media following Unix philosophy: **everything is a file**. Every post is a cryptographically signed JSON file stored on your device. Your identity is your Ed25519 public key – display names are just metadata that can collide without compromising security.

- ✅ **Everything is a file** – Posts, profiles, follows, reactions, reposts = plain JSON files
- ✅ **Your files, your rules** – Data lives in `~/.local/share/filu-x/`, never on a server
- ✅ **Cryptographic identity** – You are your pubkey; `@alice` is just a nickname
- ✅ **Thread-aware conversations** – Participant lists solve the "blind spot" problem
- ✅ **Rich interactions** – Upvotes, emoji reactions, ratings, and reposts
- ✅ **Deterministic addressing** – Post IDs are SHA256(pubkey + timestamp + content)
- ✅ **Content addressing** – Share via immutable links (`fx://bafkrei...`)
- ✅ **Protocol-agnostic** – Works with IPFS today, extensible tomorrow
- ✅ **No algorithms** – Your feed is chronological, not engagement-optimized

> "In a decentralized world, display names can collide.  
> Identity is cryptographic – your pubkey defines who you are."

---

## Filu-X Core Principle

```
┌─────────────────────────────────────────┐
│         ANY PROTOCOL → SAME RESULT      │
│                                         │
│  IPFS: bafkrei...  ─┐                   │
│  Nostr: note1...   ─┼→  DOWNLOAD  ─→  FILE  ─→  FEED │
│  HTTP: https://... ─┘        ↑           ↑      ↑     │
│                              │           │      │     │
│                         ┌────┴───────────┴──────┘     │
│                         │   PROTOCOL-AGNOSTIC CORE    │
│                         │   (crypto, templates, layout) │
│                         └─────────────────────────────┘
│                                         │
│  Feed generation is always:             │
│  1. List ~/.local/share/filu-x/...      │
│  2. Parse JSON files                    │
│  3. Validate signatures                 │
│  4. Display chronologically             │
│                                         │
│  💡 Protocol is just "transport"        │
│     Data is always the same format        │
└─────────────────────────────────────────┘
```

---

## Why This Is Elegant

| Protocol | What It Does | What Filu-X Does |
|----------|--------------|------------------|
| **IPFS** | Fetches by CID | Saves to `posts/`, parses, displays |
| **Nostr** | Fetches by event | Saves to `posts/`, parses, displays |
| **HTTP** | Fetches by URL | Saves to `posts/`, parses, displays |
| **USB** | Copies file | Saves to `posts/`, parses, displays |

**Feed code never changes:**
```python
# feed.py - completely protocol-agnostic
for post_path in layout.posts_dir.glob("*.json"):
    post = layout.load_json(post_path)  # ← Doesn't care where it came from!
    verify_signature(post)              # ← Always Ed25519
    display(post)                       # ← Always same format
```

---

## Practical Example: Multi-Protocol Feed

```
Bob's feed (3 posts from different sources):

[2026-02-20 10:00] @alice 💬
  "Alice's post"
  fx://bafkreialice...  ← Fetched from IPFS

[2026-02-20 09:30] @charlie 👍
  upvote: Great post!
  fx://bafkreicharlie... ← Fetched from Nostr

[2026-02-20 09:00] @bob 📝
  "Bob's own post"
  fx://cdd5d834ce...    ← Own post

💡 Source shown optionally, but feed works the same way
```

---

## This Is **Unix Philosophy at Its Best**

> *"Write programs to handle text streams, because that is a universal interface."*
> — Doug McIlroy

Filu-X version:
> *"Write programs to handle JSON files, because that is a universal interface."*

---

## Implications

| Benefit | Explanation |
|---------|-------------|
| **Protocol agility** | New protocol = new "downloader", no core changes |
| **Offline resilience** | Everything works without network once files are fetched |
| **Debugging** | `cat posts/abc123.json` always works |
| **Migration** | Copy files to new machine, protocol doesn't matter |
| **Censorship resistance** | If IPFS is blocked, use Nostr/HTTP/USB... |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- IPFS daemon (optional – mock mode works without it)

### Installation
```bash
# Clone and set up
git clone https://github.com/mikael1979/filu-x.git
cd filu-x
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'

# Create your identity (Ed25519 keypair)
filu-x init alice --no-password

# Create a post
filu-x post "Hello decentralized world!"

# Create a reply
filu-x post "I agree!" --reply-to bafkrei...

# React with upvote
filu-x post "!(upvote): Great point!" --reply-to bafkrei...

# Repost with comment
filu-x repost fx://bafkrei... --comment "Check this out!"

# Sync to IPFS (or mock storage if daemon unavailable)
filu-x sync -v

# Get your shareable link
filu-x link
# → fx://bafkreiabc123...

# Resolve someone else's content
filu-x resolve fx://bafkreiabc123...

# Follow another user
filu-x follow fx://bafkrei...

# View a conversation thread
filu-x thread show bafkrei...

# Follow a thread
filu-x thread follow bafkrei...

# Sync followed users' posts
filu-x sync-followed

# View your unified feed
filu-x feed
```

💡 `--no-password` stores keys unencrypted – for alpha testing only. Beta will require password-encrypted keys.

---

## 📱 Social Features (Alpha 0.0.5)

### Threads & Conversations
Filu-X solves the "blind spot" problem in decentralized networks using **participant lists**. Every post knows who is in the conversation, so you can follow threads even if you don't follow everyone.

```bash
# Reply to a post
filu-x post "This is a reply" --reply-to bafkrei...

# View a thread
filu-x thread show bafkrei...

# Follow a thread (get updates)
filu-x thread follow bafkrei...

# List followed threads
filu-x thread list

# Sync all followed threads
filu-x thread sync-all
```

### Reactions
Express yourself with compact syntax:

```bash
# Upvote with comment
filu-x post "!(upvote): Great post!" --reply-to bafkrei...

# Downvote without comment
filu-x post "!(downvote)" --reply-to bafkrei...

# Emoji reaction
filu-x post "!(react:🔥)" --reply-to bafkrei...

# Rate a post (1-5 stars)
filu-x post "!(rate:5): Excellent!" --reply-to bafkrei...
```

### Reposts
Share someone else's content with your followers:

```bash
# Simple repost
filu-x repost fx://bafkrei...

# Repost with comment
filu-x repost fx://bafkrei... --comment "Check this out!"
```

---

## 🔒 Security Model: Cryptographic Identity

Filu-X treats security as non-negotiable. Your identity is your Ed25519 public key – display names are purely cosmetic and can collide without security implications.

### Identity vs Display Name

| Concept          | Example                   | Uniqueness      | Purpose                    |
| ---------------- | ------------------------- | --------------- | -------------------------- |
| **Identity**     | `ed25519:50ad55e52c92...` | Globally unique | Cryptographic verification |
| **Display Name** | `@alice`                  | Can collide     | Human-readable reference   |

When display names collide, Filu-X shows the pubkey suffix:

```
📬 Feed (3 posts)

[2026-02-20 10:00] @alice (50ad55) 💬
  Alice's first post
  
[2026-02-20 10:05] @alice (c4ba70) 👍  ← Bob (different pubkey!)
  upvote: Great post!
  
[2026-02-20 10:10] @alice (e90b3c) 🔁  ← Charlie (yet another!)
  Repost: "Alice's first post"

⚠️  Display name collisions in feed: 'alice' used by 3 pubkeys
```

### Security Layers

| Layer         | Protection                           | Implementation                                |
| ------------- | ------------------------------------ | --------------------------------------------- |
| **Identity**  | You own your keys                    | Ed25519 keypair in `user_private/`            |
| **Storage**   | Private keys never leave your device | `user_private/` directory (never shared)      |
| **Integrity** | Every file cryptographically signed  | Ed25519 signatures verified before display    |
| **Content**   | Executables blocked by default       | Whitelist: text, images, video, audio, JSON   |
| **Network**   | No trust in external sources         | All content verified locally before rendering |

```json
{
  "id": "6bc748ecaca7877b...",
  "type": "vote",
  "value": 1,
  "content": "Great!",
  "author": "@alice",
  "pubkey": "50ad55e52c92...",
  "thread_id": "bafkreifdjx22...",
  "participants": ["50ad55e52c92...", "c4ba70..."],
  "signature": "..."
}
```

---

## 📁 Unix Philosophy: Everything is a File

Filu-X embraces the Unix philosophy where everything is a file. No databases, no proprietary formats – just plain JSON files you can read, edit, and backup with standard tools.

```
~/.local/share/filu-x/
└── data/
    ├── user_private/          # 🔒 NEVER share this
    │   ├── keys/
    │   │   ├── ed25519_private.pem   # Your secret key
    │   │   └── ed25519_public.pem    # Your public key
    │   ├── private_config.json       # Local settings
    │   └── thread_config.json        # Followed threads
    │
    ├── public/                # 🌐 Safe to publish anywhere
    │   ├── profile.json       # Your public identity
    │   ├── Filu-X.json        # Manifest of publishable files
    │   ├── follow_list.json   # Who you follow
    │   └── posts/
    │       ├── 2ffe1a58...json  # Regular post
    │       ├── 6bc748ec...json  # Upvote
    │       └── d428f20a...json  # Reaction
    │
    └── cached/                # 📦 Cached content from network
        ├── follows/            # Followed users' posts
        └── threads/            # Cached conversation threads
```

### Data Flow (File-Based)
1. **Create** → Write JSON file → Sign with Ed25519
2. **Sync** → Add file to IPFS → Get CID → Update manifest
3. **Share** → Send `fx://bafkrei...` link
4. **Resolve** → Fetch CID → Verify signature → Display content
5. **Interact** → Reply, react, repost = new JSON files
6. **Discover** → Threads via participant lists

Key insight: **Commands manipulate files** – not a database. `cat ~/.local/share/filu-x/data/public/posts/*.json` works just like any other file.

---

## ⚙️ Commands (Alpha 0.0.5)

| Command                          | Description                                |
| -------------------------------- | ------------------------------------------ |
| `filu-x init <user>`             | Create identity + Ed25519 keypair          |
| `filu-x post "text"`             | Create post (supports reactions syntax)    |
| `filu-x post --reply-to <cid>`   | Reply to a post                            |
| `filu-x repost <cid>`            | Repost with optional comment               |
| `filu-x thread show <cid>`       | Display a conversation thread              |
| `filu-x thread follow <cid>`     | Follow a thread for updates                |
| `filu-x thread list`             | List followed threads                      |
| `filu-x thread sync-all`         | Sync all followed threads                   |
| `filu-x sync`                    | Sync files to IPFS (real or mock)          |
| `filu-x sync-followed`           | Fetch posts from followed users            |
| `filu-x link`                    | Generate shareable `fx://bafkrei...` link  |
| `filu-x link --profile`          | Get profile link                           |
| `filu-x resolve <link>`          | Fetch and cryptographically verify content |
| `filu-x follow <link>`           | Follow a user (detects name collisions)    |
| `filu-x feed`                    | Show unified feed (own + followed + threads) |
| `filu-x ls`                      | List local files (offline management)      |
| `filu-x rm <post-id>`             | Delete a post                              |
| `filu-x rm --cache`               | Clear cached content                       |
| `filu-x --data-dir <path>`       | Use custom data directory                  |

---

## Multi-Profile Support

Test multiple users on same machine:

```bash
# Default profile
filu-x init alice --no-password

# Custom directory
filu-x --data-dir ./test_data/bob init bob --no-password

# Environment variable
FILU_X_DATA_DIR=./test_data/charlie filu-x init charlie --no-password
```

---

## 🗺️ Roadmap

| Version   | Stage       | Focus                                                             |
| --------- | ----------- | ----------------------------------------------------------------- |
| 0.0.1     | Alpha ✅     | Core file storage, signing, IPFS sync                             |
| 0.0.2     | Alpha ✅     | Real IPFS integration, mock fallback                              |
| 0.0.3     | Alpha ✅     | Multi-profile support (`--data-dir`), `ls` command                |
| 0.0.4     | Alpha ✅     | Deterministic IDs, cryptographic identity, collision handling     |
| **0.0.5** | **Alpha 🚀** | **Social Alpha: threads, reactions, reposts, thread following**   |
| 0.1.x     | Beta        | Password-encrypted keys, Nostr notifications, Web UI              |
| 1.0.0     | Stable      | Multi-protocol fallback, ActivityPub bridge                       |

---

## 🗑️ Data Ownership: You Control Deletion

Filu-X gives you **full control** – including safe deletion:

```bash
# Delete specific post (first 8+ chars of ID accepted)
filu-x rm 6bc748ec

# Preview before deleting
filu-x rm 6bc748ec --dry-run

# Delete without confirmation
filu-x rm 6bc748ec --force

# Clear cache from followed users
filu-x rm --cache
```

---

## 🌐 Protocol Philosophy

Filu-X embraces protocol diversity without lock-in:

| Protocol        | Role in Filu-X           | Status     |
| --------------- | ------------------------ | ---------- |
| **IPFS**        | Primary content storage  | ✅ Alpha    |
| **File system** | Local data management    | ✅ Alpha    |
| **Nostr**       | Real-time notifications  | ⏳ Beta     |
| **RSS**         | HTTP fallback for feeds  | ⏳ Beta     |
| **Freenet**     | Optional anonymity layer | ⏳ Post-1.0 |

Filu-X doesn't replace protocols – it composes them. Your data remains yours, regardless of transport layer.

---

## Known Limitations (Alpha 0.0.5)

Filu-X alpha is **development software** – not for production use.

| Limitation | Why it exists | Fixed in |
|------------|---------------|----------|
| Private keys unencrypted | Simplifies alpha development | Beta 0.1.0 (password encryption) |
| Thread discovery limited | Only root posts cached | Beta 0.1.0 (full thread fetching) |
| No private messaging | Not implemented yet | Beta 0.2.0 (encrypted groups) |

⚠️ **Do not use alpha for sensitive communications.**  
Keys are stored unencrypted – anyone with file access can impersonate you.

---

## 📜 License

Filu-X is licensed under the Apache License 2.0 – see [LICENSE](LICENSE) for details.

---

## 🙏 Contributing

Contributions are welcome! See [TODO.md](TODO.md) for development roadmap and [SECURITY.md](SECURITY.md) for security guidelines.
```


