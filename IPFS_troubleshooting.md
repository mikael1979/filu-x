# IPFS Troubleshooting Guide for Filu-X

This guide helps you set up and troubleshoot IPFS for use with Filu-X.

## Prerequisites

- IPFS installed (Kubo v0.38+)
- IPFS daemon running
- Filu-X 0.0.6 or later

## Quick Start

Check if IPFS is installed:
    ipfs --version

Start IPFS daemon (if not running):
    ipfs daemon &

Test IPFS connection:
    filu-x resolve --verbose fx://bafkreigmgbbmwvx5qe74i2sqmr3er2c7pgyjt5edjau5w57737vnld24pi

## Step-by-Step Setup

### 1. Install IPFS

Ubuntu/Debian:
    wget https://dist.ipfs.tech/kubo/v0.29.0/kubo_v0.29.0_linux-amd64.tar.gz 
    tar -xvzf kubo_v0.29.0_linux-amd64.tar.gz
    cd kubo
    sudo bash install.sh
    ipfs --version

macOS:
    brew install ipfs

Windows:
    Download from https://dist.ipfs.tech/#kubo 
    Run installer

### 2. Initialize IPFS Repository

    ipfs init

### 3. Start IPFS Daemon

Terminal 1 - Start daemon:
    ipfs daemon

Terminal 2 - Verify it is running:
    ipfs id

### 4. Test IPFS Connection

Check if Filu-X can connect:
    filu-x resolve --verbose fx://bafkreigmgbbmwvx5qe74i2sqmr3er2c7pgyjt5edjau5w57737vnld24pi

Should see:
    Connected to IPFS daemon (http://127.0.0.1:5001/api/v0 )
    Signature verified

## Common Issues and Solutions

### Issue 1: Failed to connect to IPFS daemon

Symptoms:
    IPFS daemon not available (Connection refused), using mock mode

Solutions:
Check if daemon is running:
    ps aux | grep ipfs

Start daemon:
    ipfs daemon &

Check API endpoint:
    curl http://127.0.0.1:5001/api/v0/id 

### Issue 2: Content not found for CID

Symptoms:
    Content not found for CID: bafkrei...

Solutions:
Check if content exists:
    ipfs cat bafkrei... 2&gt;/dev/null

Try to fetch from network:
    ipfs get bafkrei...

Check IPFS configuration (if behind firewall):
    ipfs config Addresses.API
    ipfs config Addresses.Gateway

For followed users - ensure they have synced:
    filu-x sync -v

### Issue 3: Manifest contains 0 posts but posts exist

Symptoms:
    Manifest contains 0 posts

Solutions:
Check the manifest directly:
    ipfs cat &lt;manifest_cid&gt; | jq '.entries | length'

Verify that the manifest has IPFS CIDs (not deterministic IDs):
    ipfs cat &lt;manifest_cid&gt; | jq '.entries[].cid'

If entries are deterministic IDs, user needs to sync:
    filu-x sync -v

### Issue 4: IPNS resolution fails

Symptoms:
    Failed to resolve manifest IPNS: Content not found for CID: ...

Solutions:
IPNS propagation takes time (20-30 seconds). Use --wait flag:
    filu-x sync-followed -v --wait 60

Check if IPNS name exists:
    ipfs name resolve &lt;ipns_name&gt;

Verify that the user has published to IPNS:
    filu-x sync -v

### Issue 5: Following does not show posts

Symptoms:
- Follow command succeeds
- sync-followed runs without errors
- Feed is empty

Solutions:
Check cache directory:
    ls -la ./data/cached/ipfs/follows/&lt;username&gt;/posts/

Verify manifest in cache:
    cat ./data/cached/ipfs/follows/&lt;username&gt;/Filu-X.json | jq '.entries | length'

Manually copy if needed (for testing):
    cp -r ./data/public/ipfs/* ./data/cached/ipfs/follows/&lt;username&gt;/

Check version mismatch:
    echo "Profile version: $(cat ./data/public/ipfs/profile.json | jq -r '.manifest_version')"
    echo "Cached version: $(cat ./data/cached/ipfs/follows/&lt;username&gt;/Filu-X.json | jq -r '.manifest_version')"

## Debugging Tools

### 1. Enable verbose output

    filu-x sync -v
    filu-x sync-followed -v
    filu-x resolve --verbose fx://bafkrei...

### 2. Check CID history

Install CID tracker:
    python3 cid_tracker.py monitor

Check for repeated CIDs:
    python3 cid_tracker.py report

### 3. Direct IPFS commands

Get file from IPFS:
    ipfs cat &lt;cid&gt;

List pins:
    ipfs pin ls

Check IPNS resolution:
    ipfs name resolve &lt;ipns_name&gt;

### 4. Check manifest versions

Local manifest:
    cat ./data/public/ipfs/Filu-X.json | jq '.manifest_version'

IPFS manifest:
    ipfs cat &lt;manifest_cid&gt; | jq '.manifest_version'

Cached manifest:
    cat ./data/cached/ipfs/follows/&lt;username&gt;/Filu-X.json | jq '.manifest_version'

## Best Practices

1. Always run filu-x sync -v after creating posts - This ensures posts are in IPFS and manifest is updated

2. Use --wait 60 for IPNS operations - IPNS propagation takes time

3. Check versions - Compare local, IPFS, and cached manifest versions

4. Keep IPFS daemon running - Filu-X falls back to mock mode if daemon is down

5. Use direct CIDs for following - More reliable than IPNS in alpha

## Still Having Issues

1. Check the Filu-X GitHub Issues: https://github.com/mikael1979/filu-x/issues

2. Run the diagnostic script:
    python3 manifest_tracker.py &lt;follower&gt; &lt;followed&gt;

3. Enable maximum verbosity:
    filu-x sync-followed -v --allow-unverified

4. Check IPFS logs:
    ipfs log tail
