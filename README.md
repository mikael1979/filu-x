         Tässä päivitetty README.md Apache 2.0 -lisenssillä:

---

```markdown
# Filu-X: Decentralized, Censorship-Resistant Social Media Extension

**Version:** 000.000.001 (Stable)  
**License:** Apache 2.0  
**Language:** English | [Suomi](README.fi.md)

---

## Philosophy

Filu-X is rooted in Unix philosophy: **do one thing well**. Share a link on social media that points to a file containing your posts and information about where else they can be found via different protocols. If one platform censors or goes down, your content remains accessible elsewhere.

> *"Write programs that do one thing and do it well. Write programs to work together."*  
> — Peter H. Salus, A Quarter-Century of Unix

Filu-X is **not a platform**. It's a file format and a set of conventions that lets you **post once and be found everywhere**.

---

## Core Concept

- Each profile is a **JSON file** (manifest)
- The file contains **links to itself** via multiple protocols (IPFS, HTTPS, Nostr, Tor...)
- The user defines **protocol priority** (which to try first)
- Followers load content in **that priority order**
- Everything is **text** (JSON) until it needs to be something else

---

## Quick Start

```bash
# Install (future)
pip install filu-x

# Create your first profile
filu-x init --username matti

# Post something
filu-x post "Hello, decentralized world!"

# Share the link anywhere
# fx://QmYourProfileHash
```

---

## Storage Modes

Filu-X supports three storage modes. Choose based on your activity level:

| Mode | Description | Best For | Max Posts |
|------|-------------|----------|-----------|
| **Single-file** | All posts in one file | Beginners, occasional posters | ~50 |
| **Linked** | References to separate post files | Active users, lots of media | Unlimited |
| **Hybrid** | Active posts (≤50) + archive reference | Moderate activity | Unlimited with archives |

### Single-file Mode
```json
{
  "version": "000.000.001",
  "mode": "single",
  "profile": {
    "username": "matti",
    "pubkey": "61050fdd097640415c9a65e85174a7a7a9bf4394d51e53e35f564264e08fcddf"
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
    "username": "matti",
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
    "username": "matti",
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
      "ipfs": "ipfs://QmArchive2025.tar.gz",
      "https": "https://example.com/archive/2025.tar.gz"
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

---

## ID System

Every post has a unique, hierarchical ID:

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
| **postHASH** | `xxxxxxxx` | First 8 chars of SHA-256 hash (integrity verification) |

Post numbers reset with each new manifest version (`000.000.002` starts at `000001`), ensuring archive paths remain stable and predictable.

---

## Linking with fx://

`fx://` is the Filu-X protocol identifier — like `http://` but specific to Filu-X manifests.

| Format | Example | Resolves To |
|--------|---------|-------------|
| **Hash** | `fx://QmFiluXManifestHash` | IPFS CID |
| **URL** | `fx://https://example.com/matti_filu-x.json` | HTTPS endpoint |
| **Post** | `fx://QmHash/000.000.001.000042` | Specific post (archived) |
| **Alias** | `fx://@matti` | DNS/NIP-05 resolution |

Share `fx://` links on any platform. If the platform censors the link text, the hash remains shareable.

---

## Architecture

Filu-X uses a **split architecture** for efficiency:

```
┌─────────────────────────────────────────┐
│         filu-x-core (shared)            │
│    IPFS, HTTP, Nostr, Crypto, Cache     │
└─────────────────────────────────────────┘
            ▲                    ▲
   ┌────────┴────────┐    ┌───────┴────────┐
   │  filu-x-client  │    │ filu-x-notifier │
   │    (CLI/GUI)    │◄──►│  (background)   │
   │  Interactive    │ IPC │  Polls updates  │
   └─────────────────┘    └─────────────────┘
```

- **Client**: User interface, posting, following management
- **Notifier**: Background daemon, polls for updates, receives real-time events
- **Core**: Shared library used by both

The notifier enables real-time updates without keeping the client open constantly.

---

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Simplicity** | Single file, clear structure, Unix philosophy |
| **Censorship Resistance** | Multi-protocol support with automatic fallbacks |
| **User Control** | Own data, own keys, own priority rules |
| **Decentralization** | No central server required |
| **Security** | Cryptographic signatures, hierarchical key management |
| **Privacy** | End-to-end encryption for private posts |
| **Persistence** | Active + archive design ensures content longevity |

---

## Privacy & Encryption

| Mode | Public | Private |
|------|--------|---------|
| **Single** | ✅ | ❌ |
| **Linked** | ✅ | ✅ |
| **Hybrid** | ✅ (active) | ✅ (archive) |

Private posts use **age** encryption with per-recipient keys. Only specified recipients can decrypt.

---

## Use Cases

- **Cross-platform persistence** → Post on X, Mastodon, Instagram — your content survives even if platforms delete it
- **Resilient profile** → IPFS primary, HTTPS fallback, Nostr real-time
- **Private conversations** → End-to-end encrypted posts for selected recipients
- **Persistent discussions** → Conversations survive platform shutdowns
- **Compromise recovery** → Revoke lost device keys without exposing master key

---

## Directory Structure

```
filu-x-data/
├── my/
│   ├── profile.json              # Your manifest
│   ├── keys/                     # Hierarchical keys
│   └── drafts/                   # Unpublished posts
├── following/                    # Followed users (slot-based)
│   ├── followed_index.json       # Central index (v000.001.001)
│   ├── user001/                  # Slot 1: Alice
│   ├── user002/                  # Slot 2: Bob
│   └── user003/                  # Slot 3: (available)
├── cache/                        # Shared media & posts
└── config/                       # Client & notifier settings
```

---

## Technical Documentation

- [Full Specification](docs/SPECIFICATION.md) — Complete protocol details
- [JSON Schema](spec/000.000.001/schema-combined.json) — Validation schemas
- [Architecture](docs/ARCHITECTURE.md) — Client, notifier, and core design
- [Examples](examples/) — Working example files

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Protocol Spec | ✅ Complete | Version 000.000.001 stable |
| Reference Client | 🚧 Alpha | Python CLI implementation |
| Notifier Daemon | 🚧 Alpha | Background update service |
| Web Client | 📋 Planned | Browser-based interface |
| Mobile Client | 📋 Planned | iOS/Android apps |

---

## Contributing

Filu-X is open source. Contributions welcome:

1. Read the [Specification](docs/SPECIFICATION.md)
2. Check [Issues](https://github.com/filu-x/filu-x/issues) for tasks
3. Submit PRs against `main` branch

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) file.

Copyright 2026 Filu-X Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

**Filu-X: Post once, be found everywhere.**



