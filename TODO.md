Tässä on päivitetty `TODO.md` versiolle 0.0.5 Alpha "Social Alpha":

```markdown
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

### 0.0.5 – Social Alpha 🚀 (CURRENT)

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
- [x] `filu-x repost <cid>` command
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

#### Bug Fixes
- [x] Removed broken repost code from `ls.py`
- [x] Fixed thread command import order
- [x] Added CID validation to all commands
- [x] Improved error messages for missing content

### 0.0.6 – Planned (Next)

#### Feed Improvements
- [ ] Thread indicators in feed (show participant count)
- [ ] Auto-discovery of threads from followed users
- [ ] Collapsible thread view in feed
- [ ] Reaction aggregation (show counts instead of individual posts)

#### Mentions & Discovery
- [ ] `@username` mentions (link to profile)
- [ ] Local mention notifications
- [ ] Hashtag support (`#topic`)
- [ ] Local search across cached posts

#### Performance
- [ ] Optimize thread cache structure
- [ ] Lazy loading for large threads
- [ ] Compress old thread caches

#### Quality of Life
- [ ] Better repost preview (show original content)
- [ ] Thread participation badge in feed
- [ ] `filu-x post --thread` to continue thread without reply_to
- [ ] Interactive thread view (expand/collapse)

## Beta Phase (0.1.x) – Next Milestone

### Security (P0)
- [ ] Password-encrypted private keys (scrypt + AES-256)
- [ ] Key rotation support
- [ ] **Private groups** – hybrid encryption for selected followers
  - [ ] AES-256-GCM symmetric encryption for content
  - [ ] Public key exchange during follow relationship setup
  - [ ] `filu-x post --group finance` – encrypt for "finance" group only
  - [ ] Group membership management (add/remove members)
  - [ ] Key re-sharing when group membership changes
- [ ] **Hierarchical key management** – master key authorizes signing subkeys
  - [ ] Subkeys used for daily operations (posts, manifests, follows)
  - [ ] Subkeys have validity periods (default: 30 days)
  - [ ] Master key can revoke compromised subkeys
  - [ ] `filu-x key rotate` – generate new subkey, revoke old
  - [ ] `filu-x key revoke <subkey-id>` – emergency revocation
  - [ ] Profile includes: `authorized_subkeys[]` with validity periods
  - [ ] Post signature includes: `subkey_id` + `master_signature_on_subkey`
  - [ ] Verification checks: subkey authorization chain to master key

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

### Social Features (P1)
- [ ] Private messaging (encrypted DMs)
- [ ] Public groups/channels
- [ ] Polls and surveys
- [ ] Rich media previews

## Stable Phase (1.0.0)

- [ ] Multi-protocol fallback (IPFS → HTTP → Nostr)
- [ ] Full thread discovery and synchronization
- [ ] ActivityPub bridge (Mastodon/Fediverse compatibility)
- [ ] Spam filtering and moderation tools
- [ ] Backup and restore utilities
- [ ] Official mobile apps

## Future Integrations (Post-1.0)

- [ ] **Freenet support** – store/retrieve content via Freenet darknet
- [ ] Tor hidden service support
- [ ] Dat/Hypercore protocol support
- [ ] Blockchain anchoring for identity (optional)
- [ ] AI-powered content recommendations (opt-in)

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🚀 | Current version |
| 🔄 | In progress |
| ⏳ | Planned |
| P0 | Critical priority |
| P1 | High priority |
| P2 | Nice to have |
```


