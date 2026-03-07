
---

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

## File Structure

### 1. Protocols and Priority
```json
{
  "protocols": {
    "priority": ["ipfs", "https", "nostr", "tor"],
    "ipfs": {
      "primary": "ipfs://QmActiveFileHash",
      "mirrors": ["ipfs://QmMirror1", "ipfs://QmMirror2"]
    },
    "https": {
      "primary": "https://example.net/filu-x.json",
      "mirrors": ["https://archive.org/filu-x.json"]
    }
  }
}
```

### 2. Profile
Two approaches:
- **Link to separate HTML page** (full creative freedom)
- **HTML template in JSON** (safe, simple)

```json
{
  "profile": {
    "name": "Matti",
    "avatar": "ipfs://QmAvatar",
    "bio": "Decentralization enthusiast",
    "template": {
      "html": "<div class='profile'><img src='{{avatar}}'/><h1>{{name}}</h1><p>{{bio}}</p></div>",
      "css": ".profile { color: blue; } .profile img { width: 100px; }"
    },
    "page": {
      "ipfs": "ipfs://QmProfilePage",
      "https": "https://matti.fi/profile.html",
      "priority": ["ipfs", "https"]
    }
  }
}
```

### 3. Active and Archive
- **Active file**: last N posts (e.g., 20 most recent)
- **Archive files**: older posts organized by ID ranges and time ranges

```json
{
  "recent": [
    {
      "id": "0000.0001.0042",
      "timestamp": "2025-03-08T14:23:00Z",
      "type": "original",
      "text": "Hello world!",
      "signature": "..."
    }
  ],
  "archive": {
    "ranges": [
      {
        "start": "0000.0000.0001",
        "end": "0000.0000.9999",
        "timerange": {
          "from": "2024-01-01T00:00:00Z",
          "to": "2024-12-31T23:59:59Z"
        },
        "location": {
          "ipfs": "ipfs://QmArchive1",
          "https": "https://archive.org/archive1.json"
        }
      }
    ]
  }
}
```

### 4. ID System
Format: `Category.Archive.Number` (0000.0000.0001 ... 0000.0000.9999 → 0000.0001.0000)

- Human-readable hierarchical index
- Indicates post age and archive location at a glance
- Automatic archive transition when number reaches 9999

### 5. Repost and Threading
```json
{
  "id": "0000.0001.0043",
  "timestamp": "2025-03-08T15:47:00Z",
  "type": "repost",
  "reaction": "👍 This is good!",
  "original": {
    "author": "npub1...",
    "postId": "0000.0000.1234",
    "timestamp": "2024-12-01T18:30:00Z",
    "location": {
      "ipfs": "ipfs://QmOriginal",
      "https": "https://example.com/post/123"
    }
  },
  "chain": {
    "depth": 2,
    "via": "0000.0001.0030"
  },
  "signature": "..."
}
```

### 6. Hierarchical Keys (HD)
```
Master key (offline cold storage)
    ├── Subkey 1 (daily use)
    ├── Subkey 2 (mobile device)
    └── Subkey 3 (backup)
```

```json
{
  "profile": {
    "master": { 
      "pubkey": "xpub1...", 
      "signature": "..." 
    },
    "active": {
      "pubkey": "xpub2...",
      "validFrom": "2025-01-01T00:00:00Z",
      "validTo": "2025-12-31T23:59:59Z",
      "signature": "xpub1:..."
    },
    "revoked": [
      {
        "pubkey": "xpub2...",
        "reason": "lost device",
        "timestamp": "2025-03-08T22:00:00Z",
        "signature": "xpub1:..."
      }
    ]
  }
}
```

## Key Principles

1. **Simplicity** - Single file, clear structure, Unix philosophy
2. **Censorship Resistance** - Multi-protocol support and automatic fallbacks
3. **User Control** - Own data, own keys, own priority rules
4. **Decentralization** - No central server required, works atop existing platforms
5. **Security** - Cryptographic signatures and hierarchical key management
6. **Persistence** - Active + archive design ensures content longevity

## Use Cases

- **Share a link on X.com or in any social media** → followers see your post even if X removes it
- **Resilient profile** → Your profile works via IPFS, with HTTPS as fallback
- **Persistent conversations** → Discussions survive even if the original platform disappears
- **Key compromise** → Revoke a lost device key without exposing your master key

## Next Steps

- [ ] Protocol specification document
- [ ] Reference client implementation
- [ ] Example application and demo
- [ ] Community feedback and iteration

---

**Filu-X: Post once, be found everywhere.**
