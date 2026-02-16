# Security Policy

## Reporting Vulnerabilities

Filu-X is currently in **alpha development** (version 0.0.4). We do not have a dedicated security team or bug bounty program.

To report security issues:
1. Open a **public GitHub Issue** at https://github.com/mikael1979/filu-x/issues
2. Tag it with `[security]` in the title
3. Describe the vulnerability and reproduction steps

⚠️ **Why public issues?**  
- Alpha software has known limitations (e.g., unencrypted keys)
- Transparency helps the community understand risks
- No sensitive user data exists yet (alpha = development only)

## Known Limitations (Alpha 0.0.4)

| Risk | Status | Mitigation |
|------|--------|------------|
| Private keys stored unencrypted | ⚠️ Known limitation | Beta will add password encryption |
| Manifests not fully verified | ⚠️ Known limitation | Beta will implement full verification |
| No rate limiting | ✅ Not applicable | No network service in alpha |

## When We'll Add Formal Security Process

We will establish a dedicated security process when:
- ✅ Beta phase begins (0.1.x) with real users
- ✅ Private data handling begins (encrypted keys)

