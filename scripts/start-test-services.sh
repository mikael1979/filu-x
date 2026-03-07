#!/bin/bash
# Käynnistä tarvittavat palvelimet testejä varten

echo "🔍 Checking test services..."

# Tarkista IPFS
if command -v ipfs &> /dev/null; then
    if ! curl -s http://127.0.0.1:5001/api/v0/id > /dev/null; then
        echo "📦 Starting IPFS daemon..."
        ipfs daemon &
        sleep 3
    else
        echo "✅ IPFS already running"
    fi
else
    echo "⚠️  IPFS not installed, tests will use mock mode"
fi

# HTTP-palvelinta ei käynnistetä automaattisesti - 
# testit käynnistävät oman tarvittaessa

echo "✅ Test services ready"
