# Filu-X

> Files as social media. Own your data. Verify everything.

[![Alpha](https://img.shields.io/badge/version-0.0.1-alpha?color=orange)](https://github.com/mikael1979/filu-x/releases)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

Filu-X is a file-based approach to decentralized social media. Every post is a cryptographically signed JSON file stored on your device. Content is addressed by its hash (`fx://bafkrei...`), enabling true permanence and verifiability.

- ✅ **Your files, your rules** – Data lives in `~/.local/share/filu-x/`, never on a server
- ✅ **Cryptographic integrity** – Every file signed with Ed25519 keys
- ✅ **Content addressing** – Share via immutable links (`fx://bafkrei...`)
- ✅ **Protocol-agnostic** – Works with IPFS today, extensible tomorrow
- ✅ **No algorithms** – Your feed is chronological, not engagement-optimized

> "Social media shouldn't require surrendering your data to platforms.  
> Filu-X gives you back ownership – one signed file at a time."

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


💡 --no-password stores keys unencrypted – for alpha testing only.
Beta will require password-encrypted keys.

🔒 Security Model
Filu-X treats security as non-negotiable:

Layer
Protection
Implementation

Storage
Private keys never leave your device
user_private/ directory (never shared)

Integrity
Every file cryptographically signed
Ed25519 signatures verified before display

Content
Executables blocked by default
Whitelist: text, images, video, audio, JSON

Network
No trust in external sources
All content verified locally before rendering

# Every post includes its own verification
{
  "content": "Hello world!",
  "pubkey": "...",
  "signature": "...",  # ← Verified before display
  "content_type": "text/plain"         # ← Whitelisted type only
}

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
        ├── follow_list.json   # Who you follow (optional sharing)
        └── posts/
            └── 20260214_120000_hello.json  # Signed post
```


```markdown
### Data flow

1. **Create post** → Sign with Ed25519
2. **Sync mode?**
   - ✅ IPFS daemon running → Push to IPFS network
   - ❌ No daemon → Store in mock cache (`~/.cache/filu-x/ipfs_mock/`)
3. **Generate link** → `fx://bafkrei...`
4. **Share link** anywhere (Twitter, Mastodon, etc.)
5. **Others resolve** → Download + cryptographically verify content
⚙️ Commands (Alpha 0.0.1)
```
```bash
Command
Description
filu-x init <user>

Create identity + Ed25519 keypair
filu-x post "text"

Create signed post (saved as JSON)
filu-x sync

Sync files to IPFS (real or mock)
filu-x link

Generate shareable fx://bafkrei... link
filu-x resolve <link>

Fetch and cryptographically verify remote content
filu-x follow <link>

Follow a user by profile link
filu-x feed

Show your feed (your posts in alpha)
🔑 Key insight: Commands manipulate files – not a database.
cat ~/.local/share/filu-x/data/public/posts/*.json works just like any other file.
```
🗺️ Roadmap
Version
Stage
Focus
0.0.1
Alpha ✅
Core file storage, signing, IPFS sync, link generation

0.1.x
Beta
Password-encrypted keys, Nostr notifications, RSS fallback

1.0.0
Stable
Multi-protocol fallback, reposts, ActivityPub bridge

See TODO.md for detailed development plan.

🌐 Protocol Philosophy
Filu-X embraces protocol diversity without lock-in:
Protocol
Role in Filu-X
Status
IPFS

Primary content storage
✅ Alpha
Nostr
Real-time notifications
⏳ Beta
RSS
HTTP fallback for feeds
⏳ Beta
Freenet
Optional anonymity layer
⏳ Post-1.0 (P2 priority)
Filu-X doesn't replace protocols – it composes them.
Your data remains yours, regardless of transport layer.

📜 License
Filu-X is licensed under the Apache License 2.0 – see LICENSE for details.

