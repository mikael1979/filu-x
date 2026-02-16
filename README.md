# Filu-X

&gt; Files as social media. Own your data. Verify everything.  
&gt; **Unix philosophy: Everything is a file.**

[![Alpha](https://img.shields.io/badge/version-0.0.4-alpha?color=orange)](https://github.com/mikael1979/filu-x/releases)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

Filu-X is a file-based approach to decentralized social media following Unix philosophy: **everything is a file**. Every post is a cryptographically signed JSON file stored on your device. Your identity is your Ed25519 public key – display names are just metadata that can collide without compromising security.

- ✅ **Everything is a file** – Posts, profiles, follows = plain JSON files
- ✅ **Your files, your rules** – Data lives in `~/.local/share/filu-x/`, never on a server  
- ✅ **Cryptographic identity** – You are your pubkey; `@alice` is just a nickname
- ✅ **Deterministic addressing** – Post IDs are SHA256(pubkey + timestamp + content)
- ✅ **Content addressing** – Share via immutable links (`fx://bafkrei...`)
- ✅ **Protocol-agnostic** – Works with IPFS today, extensible tomorrow
- ✅ **No algorithms** – Your feed is chronological, not engagement-optimized

&gt; "In a decentralized world, display names can collide.  
&gt; Identity is cryptographic – your pubkey defines who you are."

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

# Sync to IPFS (or mock storage if daemon unavailable)
filu-x sync -v

# Get your shareable link
filu-x link
# → fx://bafkreiabc123...

# Resolve someone else's content
filu-x resolve fx://bafkreiabc123...

# Follow another user
filu-x follow fx://bafkrei...

# Sync followed users' posts
filu-x sync-followed

# View your unified feed
filu-x feed
```

💡 --no-password stores keys unencrypted – for alpha testing only.
Beta will require password-encrypted keys.
🔒 Security Model: Cryptographic Identity
Filu-X treats security as non-negotiable. Your identity is your Ed25519 public key – display names are purely cosmetic and can collide without security implications.
Identity vs Display Name

| Concept          | Example                   | Uniqueness      | Purpose                    |
| ---------------- | ------------------------- | --------------- | -------------------------- |
| **Identity**     | `ed25519:50ad55e52c92...` | Globally unique | Cryptographic verification |
| **Display Name** | `@alice`                  | Can collide     | Human-readable reference   |


When display names collide, Filu-X shows the pubkey suffix:

📬 Feed (3 posts)

[2026-02-16] @alice (50ad55)     ← You
  Alice's first post
  
[2026-02-16] @alice (c4ba70) 🔁  ← Bob (different pubkey!)
  Bob's first post (also @alice)
  
[2026-02-16] @alice (e90b3c) 🔁  ← Charlie (yet another!)
  Charlie täälläkin @alice!

⚠️  Display name collisions in feed: 'alice' used by 3 pubkeys

Security Layers:

| Layer         | Protection                           | Implementation                                |
| ------------- | ------------------------------------ | --------------------------------------------- |
| **Identity**  | You own your keys                    | Ed25519 keypair in `user_private/`            |
| **Storage**   | Private keys never leave your device | `user_private/` directory (never shared)      |
| **Integrity** | Every file cryptographically signed  | Ed25519 signatures verified before display    |
| **Content**   | Executables blocked by default       | Whitelist: text, images, video, audio, JSON   |
| **Network**   | No trust in external sources         | All content verified locally before rendering |

{
  "content": "Hello world!",
  "pubkey": "50ad55e52c92...",      // ← Identity (unique)
  "author": "@alice",                // ← Display name (can collide)
  "id": "11654937a76ed84e...",       // ← Deterministic: SHA256(pubkey+time+content)
  "signature": "...",                // ← Verified before display
  "content_type": "text/plain"
}

📁 Unix Philosophy: Everything is a File
Filu-X embraces the Unix philosophy where everything is a file. No databases, no proprietary formats – just plain JSON files you can read, edit, and backup with standard tools.

```bash
~/.local/share/filu-x/
└── data/
    ├── user_private/          # 🔒 NEVER share this
    │   ├── keys/
    │   │   ├── ed25519_private.pem   # Your secret key
    │   │   └── ed25519_public.pem    # Your public key
    │   └── private_config.json       # Local settings
    │
    └── public/                # 🌐 Safe to publish anywhere
        ├── profile.json       # Your public identity
        ├── Filu-X.json        # Manifest of publishable files
        ├── follow_list.json   # Who you follow
        └── posts/
            └── 11654937a76ed84e6795d4c760d682b6.json  # Signed post (deterministic ID)
```

Data Flow (File-Based)
Create post → Write JSON file → Sign with Ed25519
Sync → Add file to IPFS → Get CID → Update manifest
Share → Send fx://bafkrei... link
Resolve → Fetch CID → Verify signature → Display content
Follow → Add entry to follow_list.json (local file)
Key insight: Commands manipulate files – not a database.
cat ~/.local/share/filu-x/data/public/posts/*.json works just like any other file.

⚙️ Commands (Alpha 0.0.4)

| Command                    | Description                                |
| -------------------------- | ------------------------------------------ |
| `filu-x init <user>`       | Create identity + Ed25519 keypair          |
| `filu-x post "text"`       | Create signed post with deterministic ID   |
| `filu-x sync`              | Sync files to IPFS (real or mock)          |
| `filu-x sync-followed`     | Fetch posts from followed users            |
| `filu-x link`              | Generate shareable `fx://bafkrei...` link  |
| `filu-x link --profile`    | Get profile link                           |
| `filu-x resolve <link>`    | Fetch and cryptographically verify content |
| `filu-x follow <link>`     | Follow a user (detects name collisions)    |
| `filu-x feed`              | Show unified feed (own + followed)         |
| `filu-x ls`                | List local files (offline management)      |
| `filu-x --data-dir <path>` | Use custom data directory                  |


Multi-Profile Support
Test multiple users on same machine:

# Default profile
filu-x init alice --no-password

# Custom directory
filu-x --data-dir ./test_data/bob init bob --no-password

# Environment variable
FILU_X_DATA_DIR=./test_data/charlie filu-x init charlie --no-password

🗺️ Roadmap

| Version   | Stage       | Focus                                                             |
| --------- | ----------- | ----------------------------------------------------------------- |
| 0.0.1     | Alpha ✅     | Core file storage, signing, IPFS sync                             |
| 0.0.2     | Alpha ✅     | Real IPFS integration, mock fallback                              |
| 0.0.3     | Alpha ✅     | Multi-profile support (`--data-dir`), `ls` command                |
| **0.0.4** | **Alpha ✅** | **Deterministic IDs, cryptographic identity, collision handling** |
| 0.1.x     | Beta        | Password-encrypted keys, Nostr notifications, Web UI              |
| 1.0.0     | Stable      | Multi-protocol fallback, reposts, ActivityPub bridge              |


See TODO.md for detailed development plan.

🌐 Protocol Philosophy
Filu-X embraces protocol diversity without lock-in:

| Protocol        | Role in Filu-X           | Status     |
| --------------- | ------------------------ | ---------- |
| **IPFS**        | Primary content storage  | ✅ Alpha    |
| **File system** | Local data management    | ✅ Alpha    |
| **Nostr**       | Real-time notifications  | ⏳ Beta     |
| **RSS**         | HTTP fallback for feeds  | ⏳ Beta     |
| **Freenet**     | Optional anonymity layer | ⏳ Post-1.0 |

Filu-X doesn't replace protocols – it composes them.
Your data remains yours, regardless of transport layer.

📜 License
Filu-X is licensed under the Apache License 2.0 – see LICENSE for details.






