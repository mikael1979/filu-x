# Filu-X

&gt; Files as social media. Own your data. Verify everything.  
&gt; **Unix philosophy: Everything is a file.**

[![Alpha](https://img.shields.io/badge/version-0.0.7-alpha?color=orange)](https://github.com/mikael1979/filu-x/releases)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

Filu-X is a file-based approach to decentralized social media following Unix philosophy: **everything is a file**. Every post is a cryptographically signed JSON file stored on your device. Your identity is your Ed25519 public key – display names are just metadata that can collide without compromising security.

- ✅ **Everything is a file** – Posts, profiles, follows, reactions, reposts = plain JSON files
- ✅ **Your files, your rules** – Data lives in `./data/` directory, never on a server
- ✅ **Cryptographic identity** – You are your pubkey; `@alice` is just a nickname
- ✅ **Thread-aware conversations** – Thread manifests with titles and descriptions
- ✅ **Two post types** – Simple posts and thread-starting posts with metadata
- ✅ **Rich interactions** – Upvotes, emoji reactions, ratings, and reposts
- ✅ **Deterministic addressing** – Post IDs are SHA256(pubkey + timestamp + content)
- ✅ **Version management** – Each manifest has `major.minor.patch.build` version
- ✅ **Content addressing** – Share via immutable links (`fx://bafkrei...`)
- ✅ **Protocol-agnostic** – Works with IPFS today, extensible tomorrow
- ✅ **No algorithms** – Your feed is chronological, not engagement-optimized

&gt; "In a decentralized world, display names can collide.  
&gt; Identity is cryptographic – your pubkey defines who you are."

---

## Filu-X Core Principle

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
│  1. List ./data/public/ipfs/posts/      │
│  2. Parse JSON files                    │
│  3. Validate signatures                 │
│  4. Display chronologically             │
│                                         │
│  💡 Protocol is just "transport"        │
│     Data is always the same format        │
└─────────────────────────────────────────┘


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

# Create a simple post
filu-x post "Hello decentralized world!"

# Create a thread (starts a new conversation)
filu-x post "First post" --title "My Discussion" --description "Let's talk about X"

# Reply to a thread
filu-x post "I agree!" --reply-to <thread_root_id>

# React with upvote
filu-x post "!(upvote): Great point!" --reply-to <post_id>

# Repost with comment
filu-x repost fx://bafkrei... --comment "Check this out!"

# Sync to IPFS
filu-x sync -v

# View a thread
filu-x thread show <thread_id>

# Follow a thread
filu-x thread follow <thread_id>

# List followed threads
filu-x thread list

# View your feed
filu-x feed

📱 Social Features (Alpha 0.0.7)
Threads & Conversations
Filu-X now supports two types of posts:
Simple posts – Standalone messages without thread context
Thread posts – Start a conversation with title and description
Each thread has its own:
Thread manifest – Contains all posts in the conversation
Thread IPNS – Permanent identifier for the thread
Participant list – Everyone who has replied
Title and description – Context for the conversation

# Start a new thread
filu-x post "First message" --title "My Topic" --description "Discussion about X"

# Reply to a thread
filu-x post "My reply" --reply-to <thread_root_id>

# View thread with all replies
filu-x thread show <thread_id>

# Follow thread for updates
filu-x thread follow <thread_id>

# List followed threads
filu-x thread list

# Sync thread updates
filu-x thread sync <thread_id>

Reactions
Express yourself with compact syntax:

# Upvote with comment
filu-x post "!(upvote): Great post!" --reply-to <post_id>

# Downvote without comment
filu-x post "!(downvote)" --reply-to <post_id>

# Emoji reaction
filu-x post "!(react:🔥)" --reply-to <post_id>

# Rate a post (1-5 stars)
filu-x post "!(rate:5): Excellent!" --reply-to <post_id>

Reposts
Share someone else's content with your followers:

# Simple repost
filu-x repost fx://bafkrei...

# Repost with comment
filu-x repost fx://bafkrei... --comment "Check this out!"

📊 Version Management
Every manifest has a version number in format major.minor.patch.build:
build: Increments on every change (0-9999)
patch: Increments when build reaches 9999
minor: Increments when patch reaches 9999
major: Increments when minor reaches 9999
This allows for up to 10^16 versions – practically unlimited!

# Check your manifest version
cat ./data/public/ipfs/Filu-X.json | jq '.manifest_version'

# Versions increase automatically on sync
filu-x sync -v  # 1 → 0.0.0.1 → 0.0.0.2

⚙️ Commands (Alpha 0.0.7)

| Command                          | Description                       |
| -------------------------------- | --------------------------------- |
| `filu-x init <user>`             | Create identity + Ed25519 keypair |
| `filu-x post "text"`             | Create simple post                |
| `filu-x post --title "T"`        | Start a new thread with title     |
| `filu-x post --reply-to <cid>`   | Reply to a post/thread            |
| `filu-x repost <cid>`            | Repost with optional comment      |
| `filu-x thread show <cid>`       | Display a conversation thread     |
| `filu-x thread follow <cid>`     | Follow a thread for updates       |
| `filu-x thread list`             | List followed threads             |
| `filu-x thread sync <cid>`       | Sync a specific thread            |
| `filu-x thread sync-all`         | Sync all followed threads         |
| `filu-x thread status <cid>`     | Show thread details               |
| `filu-x sync`                    | Sync files to IPFS                |
| `filu-x sync-followed`           | Fetch posts from followed users   |
| `filu-x sync-followed --threads` | Also fetch thread manifests       |
| `filu-x link`                    | Generate shareable link           |
| `filu-x resolve <link>`          | Fetch and verify content          |
| `filu-x follow <link>`           | Follow a user                     |
| `filu-x feed`                    | Show unified feed                 |
| `filu-x ls`                      | List local files                  |
| `filu-x rm <post-id>`            | Delete a post                     |

🗺️ Roadmap

| Version   | Stage        | Focus                                                            |
| --------- | ------------ | ---------------------------------------------------------------- |
| 0.0.1     | Alpha ✅      | Core file storage, signing, IPFS sync                            |
| 0.0.2     | Alpha ✅      | Real IPFS integration, mock fallback                             |
| 0.0.3     | Alpha ✅      | Multi-profile support (`--data-dir`), `ls` command               |
| 0.0.4     | Alpha ✅      | Deterministic IDs, cryptographic identity, collision handling    |
| 0.0.5     | Alpha ✅      | Social Alpha: threads, reactions, reposts, thread following      |
| 0.0.6     | Alpha ✅      | Version management, IPFS troubleshooting, sync improvements      |
| **0.0.7** | **Alpha 🚀** | **Thread manifests, post types, thread IPNS, conversation view** |
| 0.1.x     | Beta         | Password-encrypted keys, Nostr notifications, Web UI             |
| 1.0.0     | Stable       | Multi-protocol fallback, ActivityPub bridge                      |

Known Limitations (Alpha 0.0.7)
Filu-X alpha is development software – not for production use.

| Limitation               | Why it exists                | Fixed in                          |
| ------------------------ | ---------------------------- | --------------------------------- |
| Private keys unencrypted | Simplifies alpha development | Beta 0.1.0 (password encryption)  |
| IPNS propagation delay   | IPFS network latency         | Use `--wait` flag or direct CIDs  |
| Thread discovery limited | Only root posts cached       | Beta 0.1.0 (full thread fetching) |
| No private messaging     | Not implemented yet          | Beta 0.2.0 (encrypted groups)     |


