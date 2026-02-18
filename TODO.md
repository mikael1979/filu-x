# Filu-X Development Roadmap

## Alpha Phase (0.0.x) – Status: ✅ COMPLETE

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

## Beta Phase (0.1.x) – Next Milestone

### Security (P0)
- [ ] Password-encrypted private keys (scrypt + AES-256)
- [ ] Key rotation support
- [ ] **Private groups** – hybrid encryption for selected followers (P1)
  - [ ] AES-256-GCM symmetric encryption for content
  - [ ] Public key exchange during follow relationship setup
  - [ ] `filu-x post --group finance` – encrypt for "finance" group only
  - [ ] Group membership management (add/remove members)
  - [ ] Key re-sharing when group membership changes

### Network Features (P0)
- [ ] Nostr relay integration for real-time notifications
- [ ] RSS/Atom feed generation as HTTP fallback
- [ ] Multi-gateway fallback (ipfs.io, cf-ipfs.com, dweb.link)

### UX Improvements (P1)
- [ ] Web UI prototype (static HTML client)
- [ ] QR code generation for links
- [ ] Mobile app prototype (Flutter)



### Social Features (P1)
- [ ] Repost/Boost with attribution
  - [ ] `filu-x repost <link>` command
  - [ ] Store as `type: "repost"` with `original_post_cid`
  - [ ] Render in feed with 🔁 icon + attribution
  - [ ] Verify original post at view time (alpha limitation lifted in beta)

## Stable Phase (1.0.0)

- [ ] Multi-protocol fallback (IPFS → HTTP → Nostr)
- [ ] Reposts with cryptographic attribution
- [ ] ActivityPub bridge (Mastodon/Fediverse compatibility)

## Future Integrations (Post-1.0)

- [ ] **Freenet support** – store/retrieve content via Freenet darknet (P2 priority)
- [ ] Tor hidden service support
- [ ] Dat/Hypercore protocol support
