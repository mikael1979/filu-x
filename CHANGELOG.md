# Changelog


## [0.0.6] - 2026-02-21 (Alpha)

### Added
- **IPFS troubleshooting guide** – step-by-step instructions for IPFS setup
- **Manifest versioning** – `major.minor.patch.build` version numbers
- **Version increment on updates** – manifest version increases with each sync
- **Better sync logic** – only updates manifest when posts have changed
- **Deterministic ID to IPFS CID conversion** – automatic during sync

### Fixed
- `sync.py` now properly adds posts to IPFS before updating manifest
- Manifest version tracking for debugging
- IPNS propagation wait option (`--wait` flag)
- Support for both deterministic IDs and IPFS CIDs in sync-followed

### Changed
- Version bumped to 0.0.6
- Improved error messages and debug output
- Cache structure now uses `data/cached/ipfs/follows/`

## [0.0.5] - 2026-02-20 (Alpha)
...

## [0.0.4] - 2026-02-16 (Alpha)

### Added
- **Deterministic post IDs**: SHA256(pubkey + timestamp + content)
- **Cryptographic identity**: Identity = Ed25519 pubkey (display names are metadata)
- **Display name collision detection**: Warns when following same @name with different key
- **Multi-profile support**: `--data-dir` flag + `FILU_X_DATA_DIR` environment variable
- **Offline file management**: `filu-x ls` command (list posts without IPFS)
- **Safe post deletion**: `filu-x rm <id>` with confirmation prompts and dry-run mode
- **Cache clearing**: `filu-x rm --cache` to clear followed users' cached content

### Changed
- **Breaking**: Post IDs changed from timestamps to deterministic hashes (32-char hex)
- **Breaking**: Removed transient post_id → CID updates (IDs are now stable)
- Simplified sync logic – single ID for all contexts
- Identity verification now pubkey-based (not display name)

### Fixed
- Template rendering error for private_config.json (added missing context variables)
- Syntax error in follow.py (line 74: profile_ → profile_data)

## [0.0.3] - 2026-02-14 (Alpha)
- Multi-profile support via --data-dir flag
- filu-x ls command for offline file management
- Unified feed with cached followed posts

## [0.0.2] - 2026-02-10 (Alpha)
- Real IPFS integration with mock fallback
- Follow and feed commands

## [0.0.1] - 2026-02-04 (Alpha)
- Initial release: file-based storage, Ed25519 signing, IPFS sync
