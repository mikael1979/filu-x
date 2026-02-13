# Filu-X Development Roadmap

## Alpha Phase (0.0.x) – Status: ✅ COMPLETE

- [x] File-based storage architecture
- [x] Ed25519 signing/verification
- [x] Real IPFS integration (HTTP API)
- [x] Mock IPFS fallback
- [x] CLI commands: init, post, sync, link, resolve, follow, feed
- [x] Content-type safety validation
- [x] Basic sanitization

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
- [ ] Feed generation from followed users (sync via Nostr)

### UX Improvements (P1)
- [ ] Web UI prototype (static HTML client)
- [ ] QR code generation for links
- [ ] Mobile app prototype (Flutter)

## Stable Phase (1.0.0)

- [ ] Multi-protocol fallback (IPFS → HTTP → Nostr)
- [ ] Reposts with cryptographic attribution
- [ ] ActivityPub bridge (Mastodon/Fediverse compatibility)

## Future Integrations (Post-1.0)

- [ ] **Freenet support** – store/retrieve content via Freenet darknet (P2 priority)
- [ ] Tor hidden service support
- [ ] Dat/Hypercore protocol support
