# Changelog


## [0.0.8] - 2026-03-03 (Alpha)

### Added
- **Local ID system** – Human-friendly post identifiers
  - Format: `{name}.{manifest_version}_{post_hash_6chars}`
  - Auto-generated: `post{N}.{version}_{hash}` (e.g. `post42.0_0_0_1_a1b2c3`)
  - Thread posts: `{title}.{version}_{hash}` (e.g. `my-discussion.0_0_0_1_a1b2c3`)
  - Custom names via `--local-id` flag

- **Local storage** – Posts saved in `data/local/posts/` with friendly names
  - `filu-x local list` – List all local posts
  - `filu-x local show <local_id>` – Display a local post
  - `filu-x local info <local_id>` – Show detailed information
  - `filu-x local rename <old_id> <new_name>` – Rename a local post
  - `filu-x local rm <local_id>` – Delete local copy (IPFS version unaffected)

- **Mapping system** – `data/local/mapping.json` tracks relationships between local IDs and post IDs

- **Improved testing** – 12 passing tests for local ID functionality
  - Unit tests for ID generation
  - Integration tests for post command

### Changed
- Post template includes `local_id` field
- Manifest entries now store `local_id` alongside `cid`
- Default data directory: `./data` (instead of `~/.local/share/filu-x`)

### Fixed
- Post numbering now correctly increments with each new post
- Custom local IDs are properly sanitized (special chars → hyphens)
- Thread titles are correctly converted to URL-friendly slugs

## [0.0.7] - 2026-03-01 (Alpha)
...

## [0.0.7] - 2026-03-01 (Alpha)

### Added
- **Thread manifests** – Each thread now has a manifest with title, description, and participant list
- **Two post types** – Simple posts and thread-starting posts with metadata
- **Thread IPNS** – Permanent IPNS identifier for each thread
- **Thread manifest sync** – `sync-followed --threads` flag to fetch thread manifests
- **Thread status command** – Detailed thread information
- **Thread list with titles** – Shows thread titles in list view

### Changed
- Version bumped to 0.0.7
- `post.py` now supports `--title` and `--description` for thread creation
- `thread show` now uses thread manifest for faster loading
- `thread list` shows thread titles instead of just IDs

### Fixed
- Template handling of undefined variables (reply_to, thread_id)
- Thread manifest creation and updates
- Parent post lookup for replies (local cache first)

### Documentation
- Updated README with thread features
- Updated TODO with 0.0.7 completed items
- Added thread command examples

## [0.0.6] - 2026-02-21 (Alpha)
...

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
