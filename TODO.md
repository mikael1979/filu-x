# Filu-X TODO

**Project:** Filu-X Decentralized Social Media Extension  
**Version:** 000.000.001  
**Last Updated:** 2026-04-07

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | Critical - Blocks release |
| 🟡 | High Priority - Should have for alpha |
| 🟢 | Medium Priority - Nice to have |
| ⚪ | Low Priority - Future versions |
| ✅ | Complete |
| 🚧 | In Progress |

---

## Protocol & Specification

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Finalize ID system (manifestID.postNUM.postHASH) | 🔴 | ✅ | Stable in 000.000.001 |
| 2 | Document fx:// URI scheme | 🔴 | ✅ | Complete |
| 3 | JSON Schema validation | 🟡 | ✅ | schema-combined.json |
| 4 | Archive format (tar.gz) spec | 🟡 | ✅ | Hybrid mode |
| 5 | RFP (Ring Fragment Protocol) spec | ⚪ | 📋 | Advanced privacy feature |
| 6 | Version upgrade path documentation | 🟢 | 📋 | How to migrate manifests |

---

## Core Library (filu-x-core)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | IPFS/IPNS integration module | 🔴 | 🚧 | Add, get, resolve, publish |
| 2 | HTTP client with caching | 🔴 | 🚧 | GET/POST with etag support |
| 3 | Nostr relay connection | 🟡 | 📋 | WebSocket, event handling |
| 4 | Cryptographic functions | 🔴 | 🚧 | Keys, signatures, age encryption |
| 5 | SQLite cache management | 🟡 | 📋 | Posts, media, metadata |
| 6 | Configuration handling | 🟢 | 📋 | JSON config, defaults |
| 7 | Protocol abstraction layer | 🟡 | 📋 | Unified interface for all protocols |
| 8 | IPC implementation | 🟡 | 📋 | Unix socket / TCP localhost |

---

## Client (filu-x-client)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | CLI argument parsing | 🔴 | 🚧 | Click or argparse |
| 2 | Profile initialization | 🔴 | 🚧 | `filu-x init` command |
| 3 | Post creation and editing | 🔴 | 🚧 | Text, media, metadata |
| 4 | Manifest generation | 🔴 | 🚧 | JSON output with signatures |
| 5 | **Import from file** | 🟡 | 📋 | Load `*_filu-x.json` from filesystem |
| 6 | **Import from email** | 🟡 | 📋 | Parse manifest from email attachment |
| 7 | **Import from QR code** | 🟢 | 📋 | Scan and decode `fx://` links |
| 8 | **Export shareable manifest** | 🟡 | 📋 | Minimal manifest for sharing |
| 9 | Following management | 🟡 | 📋 | Add, remove, list followed users |
| 10 | Feed generation | 🟡 | 📋 | Aggregate posts from followed users |
| 11 | Reply and repost functionality | 🟢 | 📋 | Create reply_to and repost_of posts |
| 12 | Private post encryption | 🟢 | 📋 | age encryption for Linked/Hybrid modes |
| 13 | GUI prototype (optional) | ⚪ | 📋 | Tkinter or web-based |

---

## Notifier (filu-x-notifier)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Daemon process structure | 🟡 | 📋 | Background service, systemd integration |
| 2 | Nostr relay WebSocket | 🟡 | 📋 | Persistent connections |
| 3 | DM decryption | 🟡 | 📋 | kind 4 event handling |
| 4 | IPNS polling | 🟡 | 📋 | Periodic resolution (5 min default) |
| 5 | HTTP polling | 🟢 | 📋 | Fallback for non-IPFS users |
| 6 | Change request system | 🟡 | 📋 | Write to `requests/incoming/` |
| 7 | Notification queue | 🟢 | 📋 | Priority levels, max size limit |
| 8 | Client IPC server | 🟡 | 📋 | Respond to client queries |

---

## Documentation

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Complete specification | 🔴 | ✅ | SPECIFICATION.md |
| 2 | Architecture documentation | 🟡 | ✅ | ARCHITECTURE.md |
| 3 | API documentation | 🟢 | 📋 | Docstrings → Markdown |
| 4 | Tutorial: First post | 🟡 | 📋 | Step-by-step guide |
| 5 | Tutorial: Following users | 🟢 | 📋 | Import and setup |
| 6 | Security best practices | 🟢 | 📋 | Key management, backups |
| 7 | Troubleshooting guide | ⚪ | 📋 | Common issues and fixes |
| 8 | Contributing guidelines | 🟢 | ✅ | CONTRIBUTING.md |

---

## Testing

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Unit tests for core | 🟡 | 📋 | pytest, &gt;80% coverage |
| 2 | Integration tests | 🟢 | 📋 | IPFS, HTTP, Nostr mocks |
| 3 | JSON Schema validation tests | 🟡 | 📋 | All example files |
| 4 | End-to-end test scenario | 🟢 | 📋 | Create → Share → Import → View |
| 5 | Performance benchmarks | ⚪ | 📋 | Large manifests, many followers |

---

## Infrastructure & Tooling

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | GitHub repository setup | 🔴 | ✅ | Public repo, Apache 2.0 |
| 2 | CI/CD pipeline | 🟢 | 📋 | GitHub Actions, tests on PR |
| 3 | PyPI package | 🟢 | 📋 | `pip install filu-x` |
| 4 | Example repository | 🟡 | 📋 | Sample manifests for testing |
| 5 | Website/landing page | ⚪ | 📋 | GitHub Pages, simple HTML |

---

## Protocol Extensions (Future)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Tor hidden service support | ⚪ | 📋 | Plugin architecture |
| 2 | Arweave permanent storage | ⚪ | 📋 | Blockchain-based |
| 3 | Dat/Hypercore protocol | ⚪ | 📋 | P2P alternative to IPFS |
| 4 | RFP (Ring Fragment Protocol) | ⚪ | 📋 | Advanced privacy, small groups |
| 5 | WebRTC direct connections | ⚪ | 📋 | Real-time P2P messaging |

---

## Mobile & Web (Future)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Web client prototype | ⚪ | 📋 | Browser-based, JavaScript |
| 2 | iOS app | ⚪ | 📋 | Native or React Native |
| 3 | Android app | ⚪ | 📋 | Native or React Native |
| 4 | Progressive Web App | ⚪ | 📋 | Offline capability |

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

---

## How to Contribute

1. Pick an open task from above
2. Comment on the issue or create one
3. Discuss approach in issue before coding
4. Submit PR with tests and documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

**Last Updated:** 2026-04-07  
**Next Review:** 2026-04-14
