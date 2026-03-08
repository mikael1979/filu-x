

---

# Filu-X Specification

**Version:** 000.001.001  
**Status:** Draft  
**Last Updated:** 2025-03-09  

## 1. Introduction

Filu-X is a file format and set of conventions for decentralized, censorship-resistant social media content. It follows Unix philosophy: do one thing well. A Filu-X file contains a user's profile, recent posts, and references to archives and mirrors, enabling content to persist across platform failures or censorship.

### 1.1 Conventions

- All dates MUST be in ISO 8601 format: `YYYY-MM-DDThh:mm:ssZ`
- All IDs follow the format: `KKK.AAA.NNN` (see Section 4)
- All signatures SHOULD use Ed25519 or similar
- Files MUST be valid UTF-8 JSON

## 2. File Structure

A Filu-X file consists of these top-level sections:

```json
{
  "filux": { ... },
  "protocols": { ... },
  "profile": { ... },
  "recent": [ ... ],
  "archive": { ... },
  "keys": { ... }
}
```

All sections except `filux` are OPTIONAL but RECOMMENDED.

## 3. Filu-X Version Section

```json
{
  "filux": {
    "version": "000.001.001",
    "spec": "https://filu-x.org/spec/000.001.001",
    "lastUpdated": "2025-03-09T12:00:00Z",
    "postCount": 42,
    "generator": {
      "name": "FiluX Editor",
      "version": "000.001.001",
      "url": "https://github.com/filu-x/editor"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Filu-X version (KKK.AAA.NNN format) |
| `spec` | string | No | URL to this version's specification |
| `lastUpdated` | string | Yes | Last modification time |
| `postCount` | integer | Yes | Total number of posts (including archived) |
| `generator` | object | No | Software used to create/edit this file |

## 4. ID System

### 4.1 Format

All IDs in Filu-X follow the format: **`KKK.AAA.NNN`**

- **KKK** = Category (000-999) - for future expansion (e.g., different content types)
- **AAA** = Archive (000-999) - archive segment
- **NNN** = Number (001-999) - sequential post number within archive

### 4.2 Rules

- Numbers start at 001, not 000
- When NNN reaches 999, next post goes to next archive: `KKK.AAA.999` → `KKK.(AAA+1).001`
- IDs are immutable once assigned
- IDs SHOULD be sequential by time

### 4.3 Examples

```
000.000.001 - First post ever
000.000.042 - 42nd post
000.000.999 - Last post in first archive
000.001.001 - First post in second archive
012.003.127 - Category 12, archive 3, post 127
```

## 5. Protocols Section

```json
{
  "protocols": {
    "priority": ["ipfs", "https", "nostr"],
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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority` | array | Yes | Ordered list of protocols to try |
| `[protocol]` | object | Yes | Protocol-specific access information |
| `[protocol].primary` | string | Yes | Primary URI for this protocol |
| `[protocol].mirrors` | array | No | Backup URIs for this protocol |

### 5.1 Supported Protocols

Filu-X is protocol-agnostic. Common protocols include:

- `ipfs` - IPFS URIs (`ipfs://QmHash`)
- `https` - HTTPS URLs
- `nostr` - Nostr event IDs (`nostr:note1...`)
- `tor` - Onion services
- `dat` - Dat/Hypercore
- `arweave` - Arweave transactions

## 6. Profile Section

```json
{
  "profile": {
    "name": "Matti Example",
    "avatar": "ipfs://QmAvatarHash",
    "bio": "Decentralization enthusiast",
    "links": [
      {"label": "Website", "url": "https://matti.example"},
      {"label": "GitHub", "url": "https://github.com/matti"}
    ],
    "template": {
      "html": "<div class='profile'><img src='{{avatar}}'/><h1>{{name}}</h1><p>{{bio}}</p></div>",
      "css": ".profile { color: blue; }"
    },
    "page": {
      "ipfs": "ipfs://QmProfilePage",
      "https": "https://matti.fi/profile.html"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name |
| `avatar` | string | No | Avatar image URI |
| `bio` | string | No | Short biography |
| `links` | array | No | Social/profile links |
| `template` | object | No | HTML template for rendering |
| `page` | object | No | Link to full HTML page |

### 6.1 Template Rendering

If `template` is provided, clients SHOULD render the profile using the template with data interpolation. Supported variables:

- `{{name}}` - Profile name
- `{{avatar}}` - Avatar URI
- `{{bio}}` - Biography
- `{{#links}}` - Iterate over links array

## 7. Posts

### 7.1 Post Object Structure

```json
{
  "id": "000.001.042",
  "timestamp": "2025-03-08T14:23:00Z",
  "type": "original",
  "text": "Hello world!",
  "media": [ ... ],
  "privacy": { ... },
  "encrypted": { ... },
  "signature": "base64-signature..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Post ID (KKK.AAA.NNN) |
| `timestamp` | string | Yes | Post creation time |
| `type` | string | Yes | `original`, `repost`, or `reaction` |
| `text` | string | No | Post content (plain text) |
| `media` | array | No | Media attachments |
| `privacy` | object | No | Privacy settings |
| `encrypted` | object | No | Encrypted content |
| `signature` | string | Yes | Cryptographic signature |

### 7.2 Post Types

| Type | Description |
|------|-------------|
| `original` | New content created by user |
| `repost` | Sharing someone else's post |
| `reaction` | Simple reaction (like, emoji) |

### 7.3 Repost Structure

```json
{
  "type": "repost",
  "reaction": "👍 This is good!",
  "original": {
    "author": "npub1...",
    "postId": "000.000.1234",
    "timestamp": "2024-12-01T18:30:00Z",
    "location": {
      "ipfs": "ipfs://QmOriginal",
      "https": "https://example.com/post/123"
    }
  },
  "chain": {
    "depth": 2,
    "via": "000.001.030"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reaction` | string | No | Comment or reaction text |
| `original.author` | string | Yes | Author's public key or ID |
| `original.postId` | string | Yes | Original post ID |
| `original.timestamp` | string | Yes | Original post time |
| `original.location` | object | Yes | Where to find original |
| `chain.depth` | integer | No | How many hops (1 = direct repost) |
| `chain.via` | string | No | Who reposted it (if depth > 1) |

## 8. Media

```json
{
  "media": [
    {
      "type": "image",
      "alt": "Sunset over lake",
      "sources": {
        "ipfs": "ipfs://QmImageHash",
        "https": "https://example.com/image.jpg"
      }
    },
    {
      "type": "video",
      "poster": "ipfs://QmThumbnail",
      "sources": {
        "ipfs": "ipfs://QmVideoHash",
        "https": "https://example.com/video.mp4"
      }
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `image`, `video`, `audio`, `embed` |
| `alt` | string | No | Alternative text |
| `poster` | string | No | Thumbnail/preview image |
| `sources` | object | Yes | Protocol URIs for media |

## 9. Privacy & Encryption

### 9.1 Privacy Object

```json
{
  "privacy": {
    "visibility": "private",
    "recipients": ["npub1...", "npub2..."],
    "encryption": "age-encryption"
  }
}
```

| Visibility | Description |
|------------|-------------|
| `public` | Anyone can read |
| `private` | Only specified recipients |
| `friends` | Only friends (client-defined) |
| `group` | Only group members |

### 9.2 Encrypted Content

```json
{
  "encrypted": {
    "data": "base64-encrypted-content...",
    "keyInfo": {
      "npub1...": "encrypted-key-for-recipient1",
      "npub2...": "encrypted-key-for-recipient2"
    }
  }
}
```

The encrypted data SHOULD contain:
- Post text
- Private metadata (locations, inside jokes, etc.)
- Private media references

## 10. Active and Archive

### 10.1 Recent Posts

The `recent` array contains the most recent posts (typically 20-50). This array is updated whenever new posts are added.

### 10.2 Archive Ranges

```json
{
  "archive": {
    "ranges": [
      {
        "start": "000.000.001",
        "end": "000.000.999",
        "timerange": {
          "from": "2024-01-01T00:00:00Z",
          "to": "2024-12-31T23:59:59Z"
        },
        "postCount": 999,
        "filuxVersion": "000.000.001",
        "location": {
          "ipfs": "ipfs://QmArchive1",
          "https": "https://archive.org/archive1.json"
        }
      }
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | string | Yes | First post ID in archive |
| `end` | string | Yes | Last post ID in archive |
| `timerange.from` | string | Yes | Earliest post time |
| `timerange.to` | string | Yes | Latest post time |
| `postCount` | integer | Yes | Number of posts in archive |
| `filuxVersion` | string | Yes | Filu-X version used |
| `location` | object | Yes | Where to find archive file |

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
      "validFrom": "2025-01-01T00:00:00Z",
      "validTo": "2025-12-31T23:59:59Z",
      "signature": "xpub1master:signature..."
    },
    "revoked": [
      {
        "pubkey": "xpub3lost...",
        "reason": "Phone stolen",
        "timestamp": "2025-02-15T10:30:00Z",
        "signature": "xpub1master:signature..."
      }
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `master.pubkey` | string | Yes | Long-term master public key |
| `master.signature` | string | Yes | Self-signature of master key |
| `active` | object | Yes | Currently active signing key |
| `active.validFrom` | string | Yes | When key becomes valid |
| `active.validTo` | string | No | When key expires |
| `revoked` | array | No | Revoked keys |

### 11.1 Key Hierarchy

```
Master key (offline)
    ├── Active key (daily use)
    ├── Mobile key
    └── Backup key
```

All posts MUST be signed by an active key that is signed by the master key.

## 12. Client Behavior

### 12.1 Loading Priority

Clients SHOULD:
1. Try protocols in the order specified in `protocols.priority`
2. If primary fails, try mirrors for that protocol
3. If all mirrors fail, move to next protocol
4. Cache successful locations for future use

### 12.2 Rendering

Clients MAY:
- Render HTML templates safely (sandboxed)
- Ignore templates and show basic data
- Cache rendered profiles
- Show placeholders for encrypted content

### 12.3 Post Discovery

To find a user's posts:
1. Start with their Filu-X file URL
2. Load recent posts from `recent` array
3. For older posts, consult `archive.ranges`
4. Load archive files as needed

## 13. Security Considerations

### 13.1 Signatures

- All posts MUST be signed
- Signatures SHOULD be verified before display
- Revoked keys MUST NOT be accepted

### 13.2 Encryption

- Use well-audited encryption libraries
- Age-encryption recommended for simplicity
- PGP/compatible for broader compatibility

### 13.3 Key Storage

- Master keys SHOULD be kept offline
- Active keys SHOULD have limited validity
- Revoked keys MUST be published

## 14. Extensions

Filu-X can be extended with additional fields. Extensions SHOULD:

- Use namespaced field names (e.g., `_ext_myfeature`)
- Document their behavior
- Not break existing clients

## 15. Version History

| Version | Date | Changes |
|---------|------|---------|
| 000.001.001 | 2025-03-09 | Initial specification |

---

**Filu-X: Post once, be found everywhere.**
