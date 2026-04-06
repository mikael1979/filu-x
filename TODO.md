         Päivitetään TODO.md lukitusstrategian ja storage-managerin mukaisesti.

---

```markdown
# Filu-X TODO

**Project:** Filu-X Decentralized Social Media Extension  
**Version:** 000.000.001  
**Last Updated:** 2026-04-07

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | Critical - Blocks alpha release |
| 🟡 | High Priority - Should have for alpha |
| 🟢 | Medium Priority - Nice to have |
| ⚪ | Low Priority - Future versions |
| ✅ | Complete |
| 🚧 | In Progress |
| 📋 | Not started |

---

## Alpha Release Criteria (v000.000.001-alpha)

### Must Have (🔴 all complete or in progress)
- [ ] Core: Lock manager (cross-platform file locking)
- [ ] Core: Storage manager (slot-based following directory)
- [ ] Core: ID generator (hybrid ID format)
- [ ] Core: Manifest validator (JSON Schema)
- [ ] Core: Crypto (Ed25519 sign/verify)
- [ ] Client: CLI structure + init command
- [ ] Client: Post creation (single-file mode)
- [ ] Client: Import from file (manual sharing)
- [ ] Client: Process change requests from notifier
- [ ] Notifier: HTTP poller with change request support
- [ ] Docs: Installation instructions
- [ ] Tests: End-to-end flow (init → post → import → view)

### Should Have (🟡 for polished alpha)
- [ ] Client: Follow/unfollow commands
- [ ] Client: Feed generation
- [ ] Notifier: IPNS polling
- [ ] Tests: Unit tests for core modules

---

## Protocol & Specification

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Finalize ID system (manifestID.postNUM.postHASH) | 🔴 | ✅ | Stable in 000.000.001 |
| 2 | Document fx:// URI scheme | 🔴 | ✅ | Complete |
| 3 | JSON Schema validation | 🔴 | ✅ | schema-combined.json |
| 4 | Archive format (tar.gz) spec | 🟡 | ✅ | Hybrid mode |
| 5 | Locking protocol documentation | 🟡 | 📋 | Client vs Notifier interaction |
| 6 | Change request format spec | 🟡 | 📋 | JSON schema for request files |
| 7 | Version upgrade path | 🟢 | 📋 | How to migrate manifests |
| 8 | RFP (Ring Fragment Protocol) spec | ⚪ | 📋 | Advanced privacy feature |

---

## Core Library (filu-x-core)

### Locking & Storage (🔴 Critical)

| # | Task | Priority | Status | Notes | Blocks |
|---|------|----------|--------|-------|--------|
| 1 | **Lock manager** (`locking.py`) | 🔴 | 📋 | fcntl (Unix) + msvcrt/portalocker (Windows) | Client write, Notifier read |
| 2 | **Storage manager** (`storage.py`) | 🔴 | 📋 | Slot-based following directory, atomic writes | Following system |
| 3 | **Change request handler** | 🔴 | 📋 | Create/process `requests/incoming/*.json` | Notifier → Client flow |
| 4 | **ID generator** (`id.py`) | 🔴 | 📋 | Hybrid ID: manifestID.postNUM.postHASH | Post creation |
| 5 | **Manifest validator** | 🔴 | 📋 | JSON Schema validation | All manifest operations |

### Protocols & Crypto

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 6 | IPFS/IPNS integration | 🟡 | 🚧 | Add, get, resolve, publish |
| 7 | HTTP client with caching | 🟡 | 🚧 | GET/POST with etag/if-modified-since |
| 8 | Cryptographic functions | 🔴 | 🚧 | Ed25519 keys, sign, verify, age encryption |
| 9 | Nostr relay connection | 🟢 | 📋 | WebSocket, event handling (future) |
| 10 | Protocol abstraction layer | 🟡 | 📋 | Unified interface for all protocols |
| 11 | IPC implementation | 🟡 | 📋 | Unix socket / TCP localhost |

### Data Management

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 12 | SQLite cache management | 🟢 | 📋 | Posts, media, metadata |
| 13 | Configuration handling | 🟢 | 📋 | JSON config, defaults |
| 14 | Backup/history management | 🟢 | 📋 | Manifest version history |

---

## Client (filu-x-client)

### Core Commands (🔴 Alpha)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | CLI argument parsing (Click/argparse) | 🔴 | 🚧 | Command structure |
| 2 | `filu-x init` - Profile creation | 🔴 | 🚧 | Generate keys, create manifest |
| 3 | `filu-x post` - Create post | 🔴 | 📋 | Text, metadata, sign, save |
| 4 | `filu-x show` - Display profile | 🔴 | 📋 | Read and display manifest |
| 5 | **Import from file** | 🔴 | 📋 | Load `*_filu-x.json` from filesystem (email attachment, etc.) |
| 6 | **Process change requests** | 🔴 | 📋 | Handle `requests/incoming/` on startup |

### Following & Feed (🟡 Alpha+)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 7 | `filu-x follow` - Add user | 🟡 | 📋 | Slot allocation, index update |
| 8 | `filu-x unfollow` - Remove user | 🟡 | 📋 | Free slot, archive data |
| 9 | `filu-x feed` - Aggregate posts | 🟡 | 📋 | Collect from followed users |
| 10 | `filu-x list` - Show following | 🟢 | 📋 | Display followed_index.json |

### Import/Export (🟡 Manual sharing)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 11 | **Export shareable manifest** | 🟡 | 📋 | Minimal manifest for email/QR sharing |
| 12 | **Import from QR code** | 🟢 | 📋 | Scan and decode `fx://` links |
| 13 | Conflict resolution (duplicate username) | 🟡 | 📋 | Interactive nickname prompt |

### Advanced (⚪ Future)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 14 | Reply and repost | 🟢 | 📋 | `reply_to`, `repost_of` fields |
| 15 | Private post encryption | 🟢 | 📋 | age encryption (Linked/Hybrid) |
| 16 | GUI prototype | ⚪ | 📋 | Tkinter or web-based |

---

## Notifier (filu-x-notifier)

### Core (🟡 Alpha)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Daemon process structure | 🟡 | 📋 | Background service, systemd integration |
| 2 | **HTTP poller with change requests** | 🟡 | 📋 | etag/if-modified-since, write to `requests/incoming/` when locked |
| 3 | **Retry mechanism** | 🟢 | 📋 | Exponential backoff, max 3 retries |
| 4 | Change request creator | 🟡 | 📋 | Write JSON to `requests/incoming/` |
| 5 | Notification queue | 🟢 | 📋 | Priority levels, max size limit |

### Protocols (🟢 Alpha+)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 6 | IPNS polling | 🟢 | 📋 | Periodic resolution (5 min default) |
| 7 | Nostr relay WebSocket | 🟢 | 📋 | Persistent connections (future) |
| 8 | DM decryption | 🟢 | 📋 | kind 4 event handling (future) |

### IPC (🟡)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 9 | Client IPC server | 🟡 | 📋 | Respond to client queries |
| 10 | Status reporting | 🟢 | 📋 | Health/connection status |

---

## Security

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Active key passphrase protection | 🔴 | 📋 | Encrypt keys at rest (Fernet) |
| 2 | Master key offline workflow | 🔴 | 📋 | Document "air-gapped" process |
| 3 | Signature verification before display | 🔴 | 📋 | Prevent spoofed posts |
| 4 | Audit logging for key operations | 🟡 | 📋 | Log key usage with timestamps |
| 5 | Secure temporary file handling | 🟡 | 📋 | 0600 permissions, secure delete |

---

## Documentation

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Complete specification | 🔴 | ✅ | SPECIFICATION.md |
| 2 | Architecture documentation | 🟡 | ✅ | ARCHITECTURE.md |
| 3 | **Installation instructions** | 🔴 | 📋 | Step-by-step setup guide |
| 4 | **Tutorial: First post** | 🟡 | 📋 | Create, sign, share |
| 5 | **Tutorial: Following users** | 🟡 | 📋 | Import and setup |
| 6 | Locking protocol docs | 🟡 | 📋 | Client-Notifier interaction |
| 7 | Directory structure reference | 🟢 | 📋 | `filu-x-data/` layout |
| 8 | Security best practices | 🟢 | 📋 | Key management, backups |
| 9 | Troubleshooting guide | 🟢 | 📋 | Common issues |
| 10 | API documentation | 🟢 | 📋 | Docstrings → Markdown |
| 11 | Contributing guidelines | 🟢 | ✅ | CONTRIBUTING.md |

---

## Testing

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | **End-to-end test** | 🔴 | 📋 | init → post → import → view |
| 2 | Unit tests for core | 🟡 | 📋 | pytest, >80% coverage |
| 3 | **Lock manager tests** | 🟡 | 📋 | Concurrent access, timeout behavior |
| 4 | **Storage manager tests** | 🟡 | 📋 | Slot allocation, recovery |
| 5 | **Change request integration test** | 🟢 | 📋 | Notifier → Client flow |
| 6 | JSON Schema validation tests | 🟢 | 📋 | All example files |
| 7 | Mock IPFS/Nostr server | 🟢 | 📋 | Test fixtures |
| 8 | Load testing | ⚪ | 📋 | 1000 followers, 100 posts |
| 9 | Fuzz testing | ⚪ | 📋 | Manifest parsing |

---

## Infrastructure & Tooling

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | GitHub repository setup | 🔴 | ✅ | Public repo, Apache 2.0 |
| 2 | CI/CD pipeline | 🟢 | 📋 | GitHub Actions, tests on PR |
| 3 | PyPI package | 🟢 | 📋 | `pip install filu-x` |
| 4 | Example repository | 🟡 | 📋 | Sample manifests for testing |
| 5 | Website/landing page | ⚪ | 📋 | GitHub Pages |

---

## Protocol Extensions (Future)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Tor hidden service support | ⚪ | 📋 | Plugin architecture |
| 2 | Arweave permanent storage | ⚪ | 📋 | Blockchain-based |
| 3 | Dat/Hypercore protocol | ⚪ | 📋 | P2P alternative |
| 4 | RFP (Ring Fragment Protocol) | ⚪ | 📋 | Advanced privacy |
| 5 | WebRTC direct connections | ⚪ | 📋 | Real-time P2P |

---

## Mobile & Web (Future)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Web client prototype | ⚪ | 📋 | Browser-based |
| 2 | iOS app | ⚪ | 📋 | Native or React Native |
| 3 | Android app | ⚪ | 📋 | Native or React Native |
| 4 | Progressive Web App | ⚪ | 📋 | Offline capability |

---

## Dependency Graph

```
Core: Locking (🔴📋)
  ├─ blocks → Client: write operations
  ├─ blocks → Notifier: read operations
  └─ blocks → Change request system

Core: Storage (🔴📋)
  ├─ blocks → Client: following management
  ├─ blocks → Notifier: index updates
  └─ blocks → Import/Export

Core: ID Generator (🔴📋)
  └─ blocks → Client: post creation

Core: Validator (🔴📋)
  └─ blocks → All manifest operations

Core: Crypto (🔴🚧)
  ├─ blocks → Client: signing
  ├─ blocks → Client: verification
  └─ blocks → Security: key protection
```

---

## Completed ✅

- [x] Protocol specification v000.000.001
- [x] ID system design (manifestID.postNUM.postHASH)
- [x] Storage modes (Single, Linked, Hybrid)
- [x] fx:// URI scheme
- [x] Filename convention (username → nickname → pubkey)
- [x] Apache 2.0 license
- [x] README.md with philosophy and examples
- [x] JSON Schema draft
- [x] Architecture overview (Client + Notifier + Core)
- [x] Client-primary locking strategy

---

## How to Contribute

1. Pick an open task from above (start with 🔴)
2. Comment on the issue or create one
3. Discuss approach in issue before coding
4. Submit PR with tests and documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

**Last Updated:** 2026-04-07  
**Next Review:** 2026-04-14
```

---

**Keskeiset muutokset:**

1. **Alpha Release Criteria** -osio lisätty eksplisiittisesti
2. **Locking & Storage** erotettu omaksi kriittiseksi kokonaisuudeksi
3. **Blocks**-sarake näyttää riippuvuudet
4. **Dependency Graph** -visualisointi lisätty
5. **Security** -osio keskitettynä
6. **Change request** -taskit erikseen Clientissä ja Notifierissä
7. **Import from file** korostettu (sähköposti-scenaario)
8. **Windows-tuki** mainittu lockingissa (msvcrt/portalocker)
