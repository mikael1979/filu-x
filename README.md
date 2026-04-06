```markdown
# Filu-X: Decentralized, Censorship-Resistant Social Media Extension

## Philosophy
Filu-X is a simple idea rooted in Unix philosophy: **do one thing well**. Share a link on social media that points to a file containing your post and information about where else it can be found via different protocols. If one platform censors or goes down, the content remains accessible elsewhere.

> *"Write programs that do one thing and do it well. Write programs to work together."* — Peter H. Salus, A Quarter-Century of Unix

Filu-X is **not a platform**. It's a file format and a set of conventions that lets you post once and be found everywhere.

## Core Concept
- Each post is (or references) a **file**
- The file contains **links to itself** via multiple protocols (IPFS, HTTPS, Nostr, Tor...)
- The user defines **protocol priority**
- Followers load content in **that order**
- Everything is **text** (JSON) until it needs to be something else

## Storage Modes

Filu-X supports three storage modes, allowing users to choose between simplicity and scalability:

| Mode | Description | Best For |
|------|-------------|----------|
| **Single-file** | All posts in one file | Beginners, occasional posters (< 50 posts) |
| **Linked** | References to separate post files | Active users, lots of media |
| **Hybrid** | Active posts (≤50) + archive reference | Moderate number of posts |

### Single-file Mode
```json
{
  "version": "000.000.001",
  "mode": "single",
  "profile": {
    "name": "Matti",
    "pubkey": "61050fdd..."
  },
  "posts": [
    {
      "id": "000.000.001.000001.a1b2c3d4",
      "created": "2025-03-10T12:00:00Z",
      "text": "Hello world!"
    }
  ]
}
```

### Linked Mode
```json
{
  "version": "000.000.001",
  "mode": "linked",
  "profile": {
    "name": "Matti",
    "pubkey": "61050fdd..."
  },
  "posts": [
    {
      "id": "000.000.001.000001.a1b2c3d4",
      "urls": {
        "ipfs": "ipfs://QmPost1",
        "https": "https://example.com/posts/000001.json"
      }
    }
  ]
}
```

### Hybrid Mode
```json
{
  "version": "000.000.002",
  "mode": "hybrid",
  "profile": {
    "name": "Matti",
    "pubkey": "61050fdd..."
  },
  "posts": [
    {
      "id": "000.000.002.000002.a1b2c3d4",
      "created": "2025-03-10T12:00:00Z",
      "text": "Latest active post!"
    }
  ],
  "archive": {
    "urls": {
      "ipfs": "ipfs://QmArchive2025.tar.gz"
    },
    "range": {
      "start": "000.000.001.000001.a1b2c3d4",
      "end": "000.000.001.000040.c3d4e5f6"
    },
    "post_count": 40
  }
}
```

## ID System

### Hybrid ID Format

```
manifestID.postNUM.postHASH
000.000.001.000042.a1b2c3d4
└─────────┘ └────┘ └──────┘
   11 chars   6 chars  8 chars = 27 chars total
```

| Component | Format | Description |
|-----------|--------|-------------|
| **manifestID** | `XXX.XXX.XXX` | Manifest version (major.minor.patch) |
| **postNUM** | `XXXXXX` | Sequential number (000001-999999), resets with new manifest |
| **postHASH** | `xxxxxxxx` | First 8 chars of SHA-256 hash (integrity check) |

### Integrity Verification

```python
def verify_post_integrity(post_obj):
    # Remove ID and signature from calculation
    canonical = {k: v for k, v in sorted(post_obj.items()) 
                 if k not in ('id', 'signature')}
    data = json.dumps(canonical, sort_keys=True, separators=(',',':'))
    full_hash = hashlib.sha256(data.encode()).hexdigest()
    expected_hash = post_obj['id'].split('.')[-1]
    return full_hash.startswith(expected_hash)
```

## Filename Convention

### Priority Order
```
username --> nickname --> pubkey(16)
```

| Priority | Identifier | Format | Example |
|----------|------------|--------|---------|
| 1 | username | `username_filu-x.json` | `matti_filu-x.json` |
| 2 | nickname | `nickname_filu-x.json` | `matti42_filu-x.json` |
| 3 | pubkey(16) | `pubkey(16)_filu-x.json` | `61050fdd09764041_filu-x.json` |

### Collision Handling

When following a user and the username is already taken:

1. Client asks for a distinguishing nickname
2. If nickname is also taken → automatic numbering
3. If no nickname provided → use pubkey(16)

## Directory Structure

```
filu-x-data/
├── my/                              # Your profile
│   ├── profile.json                 # Your manifest
│   ├── keys/                        # Your keys
│   │   ├── master.asc
│   │   └── active.asc
│   └── drafts/                      # Draft posts
│
├── following/                       # Followed users (slot-based)
│   ├── followed_index.json          # Central index
│   ├── user001/                     # Slot 1
│   │   ├── .identity                # Backup mapping
│   │   ├── manifest.json
│   │   ├── history/                 # Old versions
│   │   └── cache/                   # Post cache
│   ├── user002/                     # Slot 2
│   │   └── ...
│   └── user003/                     # Slot 3 (inactive)
│
├── cache/                           # Shared cache
│   ├── media/                       # Media files (hash-based)
│   └── archives/                    # Downloaded archives
│
├── requests/                        # Change requests (notifier → client)
│   ├── incoming/
│   └── processed/
│
└── config/                          # Local settings
    ├── client.json
    └── notifier.json
```

### followed_index.json

```json
{
  "version": "000.001.001",
  "last_updated": "2025-04-07T12:00:00Z",
  "next_slot": 4,
  "free_slots": [],
  "users": {
    "user001": {
      "pubkey": "61050fdd...",
      "username": "alice",
      "nickname": "Alice Coder",
      "active": true,
      "added": "2025-04-01T10:00:00Z",
      "last_fetched": "2025-04-07T11:00:00Z",
      "last_version": "000.001.005",
      "protocols": {
        "primary": "https://alice.example.com/filu-x.json"
      }
    }
  }
}
```

## Protocols

### Protocol Structure

```json
{
  "protocols": {
    "priority": ["ipfs", "https", "nostr"],
    "ipfs": {
      "url": "ipfs://QmProfile123",
      "mirrors": ["ipfs://QmMirror1"],
      "sync": ["public", "media", "archive"]
    },
    "https": {
      "url": "https://example.com/matti_filu-x.json",
      "sync": ["public", "text-only"]
    }
  }
}
```

### fx:// Links

`fx://` is a direct link to a Filu-X manifest - similar to `http://` but Filu-X specific.

| Format | Example | Use |
|--------|---------|-----|
| Hash-based | `fx://QmFiluXManifestHash` | Direct CID reference |
| URL-based | `fx://https://example.com/matti_filu-x.json` | Direct HTTPS |
| Post reference | `fx://QmHash/000.000.001.000042` | Specific post (archived) |
| Short (alias) | `fx://@matti` | Requires DNS/NIP-05 resolution |

## Privacy & Encryption

| Mode | Public Posts | Private Posts |
|------|--------------|---------------|
| **Single** | ✅ | ❌ |
| **Linked** | ✅ | ✅ |
| **Hybrid** | ✅ (active) | ✅ (in archive) |

### Private Post Example

```json
{
  "id": "000.000.001.000043.b2c3d4e5",
  "urls": { "ipfs": "ipfs://QmPrivatePost" },
  "recipients": ["7b3d8f2a...", "9a4c2e8d..."],
  "encryption": {
    "algorithm": "age",
    "data": "base64-encrypted-content",
    "key_info": {
      "7b3d8f2a...": "encrypted-key-for-recipient1"
    }
  }
}
```

## Architecture Components

### Client (`filu-x-client`)
- CLI for user interaction
- Post creation and manifest updates
- Following management
- Feed display
- Primary lock holder (writes)

### Notifier (`filu-x-notifier`)
- Background daemon
- Polls followed users for updates
- Listens for Nostr events (future)
- Creates change requests when client has lock
- Secondary lock holder (reads only)

### Change Request System

When notifier detects an update but client holds the lock:

1. Notifier creates a change request file in `requests/incoming/`
2. Client processes pending requests on next startup/command
3. Request is moved to `requests/processed/` after handling

## Key Principles

1. **Simplicity** - Single file, clear structure, Unix philosophy
2. **Censorship Resistance** - Multi-protocol support and automatic fallbacks
3. **User Control** - Own data, own keys, own priority rules
4. **Decentralization** - No central server required, works atop existing platforms
5. **Security** - Cryptographic signatures and hierarchical key management
6. **Privacy** - End-to-end encryption for private posts
7. **Persistence** - Active + archive design ensures content longevity

## Use Cases

- **Share anywhere, persist everywhere** → Post on X, Facebook, Instagram, or any platform — your content lives on through Filu-X even if the original platform deletes it
- **Resilient profile** → Your profile works via IPFS, with HTTPS as fallback
- **Private conversations** → End-to-end encrypted posts for selected recipients
- **Persistent discussions** → Conversations survive even if the original platform disappears
- **Key compromise** → Revoke a lost device key without exposing your master key

## Example

See [`examples/single-file/filu-x.json`](examples/single-file/filu-x.json) for a complete working example.

## Next Steps

- [x] Protocol specification document
- [ ] Reference client implementation (alpha)
- [ ] Notifier daemon (alpha)
- [ ] Example application and demo
- [ ] Community feedback and iteration

---

**Filu-X: Post once, be found everywhere.**
```
