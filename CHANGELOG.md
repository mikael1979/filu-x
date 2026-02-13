# Changelog

All notable changes to Filu-X will be documented in this file.

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

### Removed
- No external dependencies beyond Python standard library + minimal packages
