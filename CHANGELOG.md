
---

## 🔧 Päivitetty `CHANGELOG.md`

```markdown
# Changelog

All notable changes to Filu-X will be documented in this file.

## [0.0.4] - 2026-02-16 (Alpha)

### Added
- **Deterministic ID generation**: Post IDs are SHA256(pubkey + timestamp + content)
- **Cryptographic identity**: Identity is Ed25519 pubkey; display names are cosmetic
- **Display name collision detection**: Warns when following users with same @name but different keys
- **Pubkey suffix in feed**: Shows `(abc123)` suffix when display names collide
- **Multi-profile support**: `--data-dir` flag and `FILU_X_DATA_DIR` environment variable
- **`filu-x ls` command**: Offline file management
- **`filu-x sync-followed` command**: Fetch posts from followed users
- **Unified feed**: Shows own posts + cached followed posts with source indicators (🔁)

### Changed
- **Breaking**: Post IDs changed from timestamps to deterministic hashes
- **Breaking**: Removed transient post_id → CID updates in sync (IDs are now stable)
- Simplified sync logic – no more CID mismatch issues
- Identity verification now based on pubkey, not display name

### Security
- Identity is now cryptographic (pubkey) rather than social (display name)
- Collision-resistant by design – same name + different key = different person

## [0.0.3] - 2026-02-14 (Alpha)

### Added
- Multi-profile support via `--data-dir` flag
- `FILU_X_DATA_DIR` environment variable support
- `filu-x ls` command for offline file management
- `filu-x sync-followed` command
- Unified feed with own + followed posts

### Fixed
- Profile isolation – multiple users can coexist on same machine

## [0.0.2] - 2026-02-10 (Alpha)

### Added
- Real IPFS integration (HTTP API to kubo daemon)
- Mock IPFS fallback when daemon unavailable
- `filu-x follow` command
- `filu-x feed` command (own posts only)
- Automatic CID update in manifest during sync

### Changed
- Improved IPFS client with auto-detection (real vs mock)

## [0.0.1] - 2026-02-04 (Alpha)

### Added
- File-based storage architecture with strict separation:
  - `user_private/` for secret keys (never shared)
  - `public/` for publishable content
- Ed25519 cryptographic signing for all user-generated content
- Mock content-addressing layer (SHA256-based CIDs) for development
- CLI commands:
  - `filu-x init` – create identity with Ed25519 keypair
  - `filu-x post` – create signed posts stored as JSON files
  - `filu-x sync` – generate content-addressed links (`fx://Qm...`)
  - `filu-x link` – generate shareable links
  - `filu-x resolve` – fetch and verify remote content
- Content-type safety validator:
  - Blocks executables (JavaScript, Python, binaries) by default
  - Sanitizes HTML/SVG/Markdown to remove scripts
  - Allows safe media types (images, video, audio, plain text)

### Security
- Strict MIME type whitelist enforced at content level
- Content inspection via `python-magic` (not just file extensions)
- Default-deny policy for unknown content types
- All signed content includes `content_type` field in payload

### Changed
- License changed from GPL3 to Apache License 2.0 for wider adoption
