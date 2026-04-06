```markdown
# Filu-X Specification

**Version:** 000.001.001  
**Status:** Draft  
**Last Updated:** 2026-04-07  

## 1. Introduction

Filu-X is a file format and set of conventions for decentralized, censorship-resistant social media content. It follows Unix philosophy: do one thing well. A Filu-X file contains a user's profile, posts, and references to archives and mirrors, enabling content to persist across platform failures or censorship.

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Censorship Resistance** | Multi-protocol support and automatic fallbacks |
| **User Control** | Own data, own keys, own priority rules |
| **Decentralization** | No central server required, works atop existing platforms |
| **Security** | Cryptographic signatures and hash-based integrity |
| **Simplicity** | Clear structure, Unix philosophy |

### 1.2 Conventions

- All dates MUST be in ISO 8601 format: `YYYY-MM-DDThh:mm:ssZ`
- All IDs follow the hybrid format: `manifestID.postNUM.postHASH` (see Section 4)
- All signatures SHOULD use Ed25519
- Files MUST be valid UTF-8 JSON

## 2. Storage Modes

Filu-X supports three storage modes, allowing users to choose between simplicity and scalability:

| Mode | Description | Best For |
|------|-------------|----------|
| **Single-file** | All posts in one file | Beginners, occasional posters (< 50 posts) |
| **Linked** | References to separate post files | Active users, lots of media |
| **Hybrid** | Active posts (≤50) + archive reference | Moderate number of posts |

### 2.1 Single-file Mode

```json
{
  "version": "000.000.001",
  "mode": "single",
  "created": "2025-04-07T12:00:00Z",
  "profile": {
    "name": "Matti",
    "pubkey": "61050fdd097640415c9a65e85174a7a7a9bf4394d51e53e35f564264e08fcddf"
  },
  "posts": [
    {
      "id": "000.000.001.000001.a1b2c3d4",
      "created": "2025-04-07T12:00:00Z",
      "text": "Hello world!"
    }
  ]
}
```

### 2.2 Linked Mode

```json
{
  "version": "000.000.001",
  "mode": "linked",
  "created": "2026-04-07T12:00:00Z",
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

### 2.3 Hybrid Mode

```json
{
  "version": "000.000.002",
  "mode": "hybrid",
  "created": "2026-04-07T12:00:00Z",
  "profile": {
    "name": "Matti",
    "pubkey": "61050fdd..."
  },
  "posts": [
    {
      "id": "000.000.002.000002.a1b2c3d4",
      "created": "2026-04-07T12:00:00Z",
      "text": "Latest active post!"
    }
  ],
  "archive": {
    "urls": {
      "ipfs": "ipfs://QmArchive2026.tar.gz"
    },
    "format": "tar.gz",
    "range": {
      "start": "000.000.001.000001.a1b2c3d4",
      "end": "000.000.001.000040.c3d4e5f6"
    },
    "post_count": 40
  }
}
```

## 3. ID System

### 3.1 Hybrid ID Format

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

### 3.2 Rules

- Numbers start at 000001, not 000000
- When postNUM reaches 999999, next post starts a new manifest version
- IDs are immutable once assigned
- IDs SHOULD be sequential by time
- manifestID increments according to semantic versioning

### 3.3 Version Components

| Component | Name | Increments when |
|-----------|------|------------------|
| First | Major | Backward incompatible change |
| Second | Minor | New feature (backward compatible) |
| Third | Patch | Fix or data update |

### 3.4 Examples

| ID | Description |
|----|-------------|
| `000.000.001.000001.a1b2c3d4` | First post in manifest 000.000.001 |
| `000.000.001.000042.b2c3d4e5` | Post #42 in same manifest |
| `000.000.002.000001.c3d4e5f6` | First post in new manifest (postNUM reset) |

### 3.5 Integrity Verification

```python
import hashlib
import json

def verify_post_integrity(post_obj):
    """
    Verify that post content matches the hash in its ID.
    """
    # Remove ID and signature from calculation
    canonical = {k: v for k, v in sorted(post_obj.items()) 
                 if k not in ('id', 'signature')}
    
    # Canonical JSON: sorted keys, no whitespace
    data = json.dumps(canonical, sort_keys=True, separators=(',',':'))
    
    # Calculate hash
    full_hash = hashlib.sha256(data.encode()).hexdigest()
    
    # Get hash part from ID (last 8 chars after dot)
    expected_hash = post_obj['id'].split('.')[-1]
    
    # Check that full_hash starts with expected 8 chars
    return full_hash.startswith(expected_hash)
```

## 4. File Structure

A Filu-X file consists of these top-level sections:

```json
{
  "version": "000.000.001",
  "mode": "single",
  "created": "2026-04-07T12:00:00Z",
  "updated": "2026-04-07T12:00:00Z",
  "profile": { ... },
  "protocols": { ... },
  "posts": [ ... ],
  "archive": { ... },
  "statistics": { ... },
  "signature": { ... }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Filu-X version (XXX.XXX.XXX format) |
| `mode` | string | Yes | Storage mode: `single`, `linked`, or `hybrid` |
| `created` | string | Yes | ISO8601 creation timestamp |
| `updated` | string | No | ISO8601 last update timestamp |
| `profile` | object | Yes | User profile information |
| `protocols` | object | No | Protocol-specific access information |
| `posts` | array | No | Posts (format depends on mode) |
| `archive` | object | No | Archive information (hybrid mode only) |
| `statistics` | object | No | Post statistics |
| `signature` | object | No | Cryptographic signature |

## 5. Profile Section

```json
{
  "profile": {
    "username": "matti",
    "nickname": "matti_coder",
    "pubkey": "61050fdd097640415c9a65e85174a7a7a9bf4394d51e53e35f564264e08fcddf",
    "name": "Matti Meikäläinen",
    "bio": "Decentralization enthusiast",
    "avatar": "ipfs://QmAvatarHash",
    "website": "https://matti.example",
    "created": "2026-01-01T12:00:00Z",
    "updated": "2026-04-07T12:00:00Z"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pubkey` | string | Yes | User's public key (64 hex chars) |
| `username` | string | No | Globally unique identifier |
| `nickname` | string | No | Human-readable name (can have duplicates) |
| `name` | string | No | Real name |
| `bio` | string | No | Short biography |
| `avatar` | string | No | Avatar image URI |
| `website` | string | No | Personal website |
| `created` | string | No | Profile creation time |
| `updated` | string | No | Profile last update |

## 6. Protocols Section

```json
{
  "protocols": {
    "priority": ["ipfs", "https", "nostr"],
    "ipfs": {
      "url": "ipfs://QmProfile123",
      "mirrors": ["ipfs://QmMirror1", "ipfs://QmMirror2"],
      "sync": ["public", "media", "archive"]
    },
    "https": {
      "url": "https://example.com/matti_filu-x.json",
      "mirrors": ["https://archive.org/matti_filu-x.json"],
      "sync": ["public", "text-only"]
    },
    "nostr": {
      "url": "nostr:note1abc123",
      "sync": ["recent"]
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority` | array | Yes | Ordered list of protocols to try |
| `[protocol].url` | string | Yes | Primary URL for this protocol |
| `[protocol].mirrors` | array | No | Backup URLs |
| `[protocol].sync` | array | No | What content is synced |

### 6.1 Supported Protocols

| Protocol | Prefix | Use Case |
|----------|--------|----------|
| `ipfs` | `ipfs://` | Long-term, decentralized storage |
| `https` | `https://` | Traditional web (fallback) |
| `nostr` | `nostr:` | Fast, relay-based distribution |
| `tor` | `http://` (onion) | Anonymous, hidden services |

### 6.2 fx:// Links

`fx://` is a direct link to a Filu-X manifest - similar to `http://` but Filu-X specific.

| Format | Example | Use |
|--------|---------|-----|
| Hash-based | `fx://QmFiluXManifestHash` | Direct CID reference |
| URL-based | `fx://https://example.com/matti_filu-x.json` | Direct HTTPS |
| Post reference | `fx://QmHash/000.000.001.000042` | Specific post (archived) |
| Short (alias) | `fx://@matti` | Requires DNS/NIP-05 resolution |

## 7. Posts

### 7.1 Post Object Structure (Single-file Mode)

```json
{
  "id": "000.000.001.000042.a1b2c3d4",
  "created": "2026-04-07T12:00:00Z",
  "updated": "2026-04-07T12:00:00Z",
  "text": "Hello world!",
  "subject": "Greetings",
  "language": "en",
  "media": [
    {
      "type": "image",
      "urls": {
        "ipfs": "ipfs://QmImageHash",
        "https": "https://example.com/image.jpg"
      },
      "alt": "Sunset over lake",
      "caption": "Beautiful evening",
      "width": 1920,
      "height": 1080
    }
  ],
  "reply_to": "000.000.001.000041.b2c3d4e5",
  "repost_of": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Full hybrid ID |
| `created` | string | Yes | ISO8601 creation timestamp |
| `updated` | string | No | ISO8601 last update |
| `text` | string | No | Post content |
| `subject` | string | No | Post title |
| `language` | string | No | BCP47 language code |
| `media` | array | No | Media attachments |
| `reply_to` | string | No | Parent post ID |
| `repost_of` | string | No | Original post ID |

### 7.2 Post Reference (Linked Mode)

```json
{
  "id": "000.000.001.000042.a1b2c3d4",
  "urls": {
    "ipfs": "ipfs://QmPostHash",
    "https": "https://example.com/posts/000042.json"
  },
  "summary": "Hello world!",
  "created": "2026-04-07T12:00:00Z"
}
```

### 7.3 Repost Structure

```json
{
  "id": "000.000.001.000043.b2c3d4e5",
  "created": "2026-04-07T13:00:00Z",
  "type": "repost",
  "reaction": "👍 This is good!",
  "original": {
    "author": "npub1...",
    "postId": "000.000.001.000042.a1b2c3d4",
    "timestamp": "2026-04-07T12:00:00Z",
    "location": {
      "ipfs": "ipfs://QmOriginal",
      "https": "https://example.com/post/042"
    }
  },
  "chain": {
    "depth": 2,
    "via": "000.000.001.000030.c3d4e5f6"
  }
}
```

## 8. Privacy & Encryption

### 8.1 Privacy Rules by Mode

| Mode | Public Posts | Private Posts |
|------|--------------|----------------|
| **Single** | ✅ | ❌ |
| **Linked** | ✅ | ✅ |
| **Hybrid** | ✅ (active) | ✅ (in archive) |

### 8.2 Public Post

```json
{
  "id": "000.000.001.000042.a1b2c3d4",
  "privacy": {
    "visibility": "public"
  },
  "text": "This is a public post"
}
```

### 8.3 Private Post (Linked Mode)

```json
// In main manifest:
{
  "posts": [
    {
      "id": "000.000.001.000043.b2c3d4e5",
      "urls": {
        "ipfs": "ipfs://QmPrivatePost"
      },
      "recipients": [
        "7b3d8f2a1c5e9b4a6d2f8c3e1a7b5d9f4c2a8e6d1b3f7a5c9e2d4b6f8a1c3e5d7"
      ],
      "encryption": {
        "algorithm": "age",
        "data": "base64-encrypted-content",
        "key_info": {
          "7b3d8f2a...": "encrypted-key-for-recipient"
        }
      }
    }
  ]
}

// Actual post file (encrypted)
{
  "id": "000.000.001.000043.b2c3d4e5",
  "created": "2026-04-07T13:00:00Z",
  "encrypted": {
    "data": "base64-encrypted-content..."
  }
}
```

## 9. Filename Convention

### 9.1 Priority Order

```
username --> nickname --> pubkey(16)
```

| Priority | Identifier | Format | Example |
|----------|------------|--------|---------|
| 1 | username | `username_filu-x.json` | `matti_filu-x.json` |
| 2 | nickname | `nickname_filu-x.json` | `matti42_filu-x.json` |
| 3 | pubkey(16) | `pubkey(16)_filu-x.json` | `61050fdd09764041_filu-x.json` |

### 9.2 Sanitization

```python
import re

def sanitize_filename(name: str) -> str:
    """Remove problematic characters from filename."""
    safe = re.sub(r'[^a-z0-9_-]', '_', name.lower())
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')
```

## 10. Directory Structure

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
│   └── user002/                     # Slot 2
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

### 10.1 followed_index.json

```json
{
  "version": "000.001.001",
  "last_updated": "2026-04-07T12:00:00Z",
  "next_slot": 3,
  "free_slots": [],
  "users": {
    "user001": {
      "pubkey": "61050fdd...",
      "username": "alice",
      "nickname": "Alice Coder",
      "active": true,
      "added": "2026-04-01T10:00:00Z",
      "last_fetched": "2026-04-07T11:00:00Z",
      "last_version": "000.001.005",
      "protocols": {
        "primary": "https://alice.example.com/filu-x.json"
      }
    }
  }
}
```

## 11. Hierarchical Keys

```json
{
  "keys": {
    "master": {
      "pubkey": "xpub1master...",
      "signature": "self-signature..."
    },
    "active": {
      "pubkey": "xpub2daily...",
      "validFrom": "2026-01-01T00:00:00Z",
      "validTo": "2026-12-31T23:59:59Z",
      "signature": "xpub1master:signature..."
    },
    "revoked": [
      {
        "pubkey": "xpub3lost...",
        "reason": "Phone stolen",
        "timestamp": "2026-02-15T10:30:00Z",
        "signature": "xpub1master:signature..."
      }
    ]
  }
}
```

### 11.1 Key Hierarchy

```
Master key (offline cold storage)
    ├── Active key (daily use)
    ├── Mobile key
    └── Backup key
```

All posts MUST be signed by an active key that is signed by the master key.

### 11.2 Key Security

- Master keys SHOULD be kept offline
- Active keys SHOULD be encrypted at rest
- Active keys SHOULD have limited validity period
- Revoked keys MUST be published in the manifest

## 12. Change Request System

When notifier detects an update but client holds the lock, it creates a change request:

```json
{
  "request_id": "1744123456_user001",
  "created": "2026-04-07T12:00:00Z",
  "type": "update_manifest",
  "target_slot": "user001",
  "data": {
    "new_manifest": { ... },
    "version": "000.001.006"
  },
  "retry_count": 0
}
```

### 12.1 Locking Strategy

| Actor | Lock Type | If Lock Held |
|-------|-----------|--------------|
| Client (write) | `LOCK_EX` | Wait (max 5s) |
| Notifier (read) | `LOCK_SH` | Create change request |

## 13. Client Behavior

### 13.1 Loading Priority

Clients SHOULD:
1. Try protocols in the order specified in `protocols.priority`
2. If primary fails, try mirrors for that protocol
3. If all mirrors fail, move to next protocol
4. Cache successful locations for future use

### 13.2 Post Discovery

To find a user's posts:
1. Start with their Filu-X file URL
2. Load posts from `posts` array (depends on mode)
3. For older posts in hybrid mode, consult `archive.ranges`
4. Load archive files as needed

### 13.3 Change Request Processing

Clients SHOULD:
1. Check for pending requests on startup
2. Process requests in FIFO order
3. Acquire exclusive lock before processing
4. Move processed requests to `processed/` directory

## 14. Security Considerations

### 14.1 Signatures

- All posts MUST be signed
- Signatures SHOULD be verified before display
- Revoked keys MUST NOT be accepted

### 14.2 Encryption

- Use well-audited encryption libraries (Age recommended)
- Encrypt active keys at rest
- Never store private keys unencrypted

### 14.3 Key Storage

- Master keys SHOULD be kept offline
- Active keys SHOULD have limited validity (e.g., 1 year)
- Revoked keys MUST be published

## 15. Version History

| Version | Date | Changes |
|---------|------|---------|
| 000.001.001 | 2026-04-07 | Initial specification with hybrid IDs, storage modes, slot-based following, and change request system |

---

**Filu-X: Post once, be found everywhere.**
```
