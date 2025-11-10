#!/bin/bash

echo "================================"
echo "Coinbase API Key Quick Check"
echo "================================"
echo

# Check API key format
echo "1. Checking API_KEY format..."
api_key=$(grep "^API_KEY=" .env | cut -d= -f2)

if [[ $api_key == organizations/* ]]; then
    echo "   ✅ API Key format looks correct"
    echo "   Key: ${api_key:0:50}..."
else
    echo "   ❌ API Key should start with 'organizations/'"
    echo "   Current: $api_key"
fi

echo

# Check private key format
echo "2. Checking API_SECRET format..."
if grep -q "BEGIN EC PRIVATE KEY" .env; then
    echo "   ✅ Private key has correct BEGIN marker"
else
    echo "   ❌ Private key should contain 'BEGIN EC PRIVATE KEY'"
fi

if grep -q "END EC PRIVATE KEY" .env; then
    echo "   ✅ Private key has correct END marker"
else
    echo "   ❌ Private key should contain 'END EC PRIVATE KEY'"
fi

echo

# Check for common issues
echo "3. Common issues check..."
if grep -q '\\\\n' .env; then
    echo "   ⚠️  Found escaped newlines - we handle this automatically"
else
    echo "   ✅ No escaped newlines found"
fi

echo
echo "================================"
echo "Next Steps:"
echo "================================"
echo "1. If this is a NEW API key (created <5 min ago):"
echo "   → Wait 5 minutes, then run: python3 test_coinbase_connection.py"
echo
echo "2. If key is old and still failing:"
echo "   → Read: COINBASE_401_TROUBLESHOOTING.md"
echo "   → Most likely: Wrong API type (need 'Advanced Trade', not 'Coinbase Pro')"
echo
echo "3. To create new API key:"
echo "   → Go to: https://www.coinbase.com/settings/api"
echo "   → Delete old key, create new 'Advanced Trade' key"
echo

