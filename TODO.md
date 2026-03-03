# Filu-X Development Roadmap

## Alpha Phase (0.0.x)

### 0.0.1 – Core Foundation ✅
- [x] File-based storage architecture (Unix philosophy)
- [x] Ed25519 signing/verification
- [x] Mock IPFS for development
- [x] CLI: init, post, sync, link, resolve
- [x] Content-type safety validation

### 0.0.2 – Real IPFS ✅
- [x] Real IPFS integration (HTTP API)
- [x] Mock IPFS fallback
- [x] Auto-detection of IPFS daemon

### 0.0.3 – Multi-Profile ✅
- [x] `--data-dir` flag for multiple profiles
- [x] `FILU_X_DATA_DIR` environment variable
- [x] `filu-x ls` command
- [x] `filu-x sync-followed` command
- [x] Unified feed (own + followed)

### 0.0.4 – Cryptographic Identity ✅
- [x] Deterministic ID generation (SHA256)
- [x] Pubkey-based identity (display names cosmetic)
- [x] Display name collision detection
- [x] Collision-aware feed rendering

### 0.0.5 – Social Alpha ✅

#### Threads & Conversations
- [x] Thread-aware participant lists (solves blind spot problem)
- [x] `reply_to` and `thread_id` in post schema
- [x] `participants` list for thread discovery
- [x] `filu-x thread show` – view conversation threads
- [x] `filu-x thread sync` – cache thread root locally
- [x] `filu-x thread follow/unfollow` – manage thread subscriptions
- [x] `filu-x thread list` – list followed threads
- [x] `filu-x thread sync-all` – sync all followed threads
- [x] `filu-x thread status` – show thread details

#### Reactions
- [x] Compact syntax `!(action)[: comment]`
- [x] Upvote/downvote (`!(upvote)`, `!(downvote)`)
- [x] Emoji reactions (`!(react:🔥)`)
- [x] Numeric ratings (`!(rate:5)`)
- [x] Reaction rendering in feed with icons

#### Reposts
- [x] `filu-x repost &lt;cid&gt;` command
- [x] Optional comment with repost
- [x] `type: "repost"` in post schema
- [x] Feed rendering with 🔁 icon
- [x] Original post attribution

#### Infrastructure
- [x] Version bump to 0.0.5
- [x] `ls.py` repost rendering fix
- [x] Thread cache directory structure
- [x] Thread configuration storage
- [x] Updated documentation (README, TODO)
- [x] Sneakernet test (USB stick simulation)

#### Bug Fixes
- [x] Removed broken repost code from `ls.py`
- [x] Fixed thread command import order
- [x] Added CID validation to all commands
- [x] Improved error messages for missing content

### 0.0.6 – Version Management & IPFS Stability ✅

#### Version Management
- [x] Manifest versioning (`major.minor.patch.build`)
- [x] Version increment on each sync
- [x] Version display in debug output
- [x] Version tracking in cache

#### Sync Improvements
- [x] Proper post → IPFS → manifest update order
- [x] Deterministic ID to IPFS CID conversion during sync
- [x] Skip manifest update when no changes
- [x] `--wait` flag for IPNS propagation
- [x] Verbose output improvements

#### Cache Structure
- [x] Protocol-specific cache directories (`cached/ipfs/follows/`)
- [x] Last sync timestamp tracking
- [x] Manifest version in cache
- [x] IPNS name caching

#### Documentation
- [x] **IPFS Troubleshooting Guide** (`IPFS_troubleshooting.md`)
- [x] Step-by-step IPFS setup instructions
- [x] Common issues and solutions
- [x] Debugging tools and commands
- [x] Version management documentation in README

#### Bug Fixes
- [x] Fixed sync.py post ordering
- [x] Fixed manifest version increment logic
- [x] Fixed cache path inconsistencies
- [x] Improved error messages for IPFS failures

### 0.0.7 – Thread Manifests & Post Types 🚀 (CURRENT)

#### Thread Manifests
- [x] Thread manifest structure (title, description, participants)
- [x] Thread IPNS for permanent thread addressing
- [x] Thread manifest storage in `cached/threads/`
- [x] Thread manifest sync with `--threads` flag
- [x] Thread manifest display in `thread show`

#### Post Types
- [x] Two post types: `simple` and `thread`
- [x] Thread posts with title and description
- [x] Simple posts for standalone content
- [x] Reply detection and thread joining

#### Thread Commands
- [x] `thread show` with thread manifest support
- [x] `thread status` for detailed thread info
- [x] `thread list` with thread titles
- [x] `thread sync` with thread manifest creation

#### Infrastructure
- [x] `layout.py` thread path methods
- [x] `post.py` thread creation and reply handling
- [x] `thread.py` ThreadManifest class
- [x] `sync_followed.py` thread manifest sync
- [x] Updated templates for post types

#### Documentation
- [x] Updated README with thread features
- [x] Updated TODO with completed items
- [x] Command examples for thread usage

### 0.0.8 – Code Quality & Testing 🚧 (IN PROGRESS)

#### Testing Infrastructure
- [ ] **Unit tests for core modules**
  - [ ] `test_crypto.py` – Ed25519 signing/verification
  - [ ] `test_id_generator.py` – deterministic ID generation
  - [ ] `test_resolver.py` – link parsing and content resolution
  - [ ] `test_layout.py` – storage layout and path management
  - [ ] `test_thread_manifest.py` – thread manifest operations

- [ ] **Integration tests**
  - [ ] End-to-end post creation flow
  - [ ] Thread creation and reply chain
  - [ ] Sync and resolve workflow
  - [ ] Follow/unfollow user flow

- [ ] **Test fixtures and mocks**
  - [ ] Mock IPFS client for testing
  - [ ] Sample post/profile data fixtures
  - [ ] Temporary directory management

#### Code Quality
- [ ] **Remove debug output**
  - [ ] Replace `print()` with proper logging
  - [ ] Add `--debug` flag for verbose output
  - [ ] Clean up `feed.py` debug prints

- [ ] **Fix version number inconsistencies**
  - [ ] Update `__init__.py`: `__version__ = "0.0.7"`
  - [ ] Update `cli/__init__.py`: `version="0.0.7"`
  - [ ] Update `pyproject.toml` version
  - [ ] Add version consistency check to CI

- [ ] **Refactor large modules**
  - [ ] Split `thread.py` into smaller files
  - [ ] Move `ThreadManifest` to `core/thread_manifest.py`
  - [ ] Move `ThreadManager` to `core/thread_manager.py`
  - [ ] Separate CLI commands from business logic

- [ ] **Fix circular imports**
  - [ ] Move shared classes to `core/` directory
  - [ ] Use lazy imports where necessary

#### Documentation Cleanup
- [ ] **Standardize language**
  - [ ] Translate Finnish comments to English
  - [ ] Translate French comments to English
  - [ ] Remove "UUSI", "KORJATTU" markers
  - [ ] Add proper docstrings to all public functions

### 0.0.9 – Protocol Grouping & JSON Schema 🚧 (IN PROGRESS)

#### Feed Improvements
- [ ] Thread indicators in feed (show participant count)
- [ ] Auto-discovery of threads from followed users
- [ ] Collapsible thread view in feed
- [ ] Reaction aggregation (show counts instead of individual posts)
- [ ] Better handling of deterministic IDs in feed

#### Mentions & Discovery
- [ ] `@username` mentions (link to profile)
- [ ] Local mention notifications
- [ ] Hashtag support (`#topic`)
- [ ] Local search across cached posts
- [ ] User discovery via shared follows

#### Performance
- [ ] Optimize thread cache structure
- [ ] Lazy loading for large threads
- [ ] Compress old thread caches
- [ ] Parallel post fetching in sync-followed

#### Quality of Life
- [ ] Better repost preview (show original content)
- [ ] Thread participation badge in feed
- [ ] Interactive thread view (expand/collapse)
- [ ] Progress bar for long sync operations

#### Thread Enhancements
- [ ] Thread subscription notifications
- [ ] Thread metadata editing (title/description)
- [ ] Thread pinning
- [ ] Thread moderation tools



#### Protocol Restructuring
- [ ] **Post JSON restructuring** – Group all protocol-specific fields under `protocols` object
  - [ ] Move `cid` → `protocols.ipfs.cid`
  - [ ] Move `http_url` → `protocols.http.url`
  - [ ] Move `ipns`/`thread_ipns` → `protocols.ipns.name` (under ipfs)
  - [ ] Add `protocols.ipfs.gateway` field
  - [ ] Add `protocols.http.mirrors` array for multiple HTTP sources
  - [ ] Prepare structure for future protocols (Nostr, Freenet, etc.)

#### JSON Schema (Optional but Recommended)
- [ ] **Create schema files** for validation and documentation
  - [ ] `schemas/post-v0.0.8.json` – Post structure validation
  - [ ] `schemas/manifest-v0.0.8.json` – Manifest structure
  - [ ] `schemas/thread_manifest-v0.0.8.json` – Thread manifest structure
  
- [ ] **Publish schemas to IPNS** (updateable pointer)
  - [ ] Create IPNS key: `ipfs key gen --type=ed25519 schemas`
  - [ ] Publish: `ipfs name publish --key=schemas /ipfs/&lt;cid&gt;`
  - [ ] Update templates to use: `https://ipfs.io/ipns/&lt;ipns&gt;/post-v0.0.8.json`
  - [ ] Document schema IPNS in README

- [ ] **Add validation** (optional, can be disabled)
  - [ ] `filu-x validate &lt;file&gt;` – Validate JSON against schema
  - [ ] Validate before `sync` (warn if invalid)
  - [ ] Skip validation with `--no-validate`

#### Migration Tools
- [ ] **Create migration command**: `filu-x migrate --to-format 0.0.8`
  - [ ] Convert old flat format to new `protocols` structure
  - [ ] Preserve all existing data
  - [ ] Create backup before migration
  - [ ] Update manifest entries

#### Infrastructure
- [ ] Update `post.json.j2` template
- [ ] Update `manifest.json.j2` template  
- [ ] Update `post.py` to use new structure
- [ ] Update `resolver.py` to read from `protocols.*`
- [ ] Update tests for new format

## Beta Phase (0.1.x) – Next Milestone

### Security (P0)
- [ ] Password-encrypted private keys (scrypt + AES-256)
- [ ] Key rotation support
- [ ] **Private groups** – hybrid encryption for selected followers
- [ ] **Hierarchical key management** – master key authorizes signing subkeys

### Perfect Privacy (P0) 🔐
- [ ] **All posts always encrypted**
- [ ] **Feed decryption** – automatic decryption with own key
- [ ] **Plausible deniability** – all posts look identical
- [ ] **Key management** – public keys in profiles

### Network Features (P0)
- [ ] Nostr relay integration for real-time notifications
- [ ] RSS/Atom feed generation as HTTP fallback
- [ ] Multi-gateway fallback (ipfs.io, cf-ipfs.com, dweb.link)
- [ ] Full thread discovery (fetch all replies from participants)

### UX Improvements (P1)
- [ ] Web UI prototype (static HTML client)
- [ ] QR code generation for links
- [ ] Mobile app prototype (Flutter)
- [ ] Desktop notifications for mentions/replies

## Stable Phase (1.0.0)

- [ ] Multi-protocol fallback (IPFS → HTTP → Nostr)
- [ ] Full thread discovery and synchronization
- [ ] ActivityPub bridge (Mastodon/Fediverse compatibility)
- [ ] Spam filtering and moderation tools
- [ ] Backup and restore utilities
- [ ] Official mobile apps

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🚀 | Current version |
| 🚧 | In progress |
| ⏳ | Planned |
| 🔐 | Privacy feature |
| P0 | Critical priority |
| P1 | High priority |
