#!/usr/bin/env python3
"""
Comprehensive Kraken API Diagnostic Tool
Tests every aspect of Kraken authentication
"""

import time
import hmac
import hashlib
import base64
import requests
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

def print_section(title):
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Style.RESET_ALL}\n")

def get_signature_debug(url_path, data, secret):
    """Generate signature with debug output"""
    print(f"{Fore.YELLOW}Signature Generation Debug:{Style.RESET_ALL}")
    print(f"  1. URL Path: {url_path}")
    print(f"  2. Data: {data}")
    print(f"  3. Nonce: {data['nonce']}")
    
    # Step 1: URL encode the data
    postdata = urlencode(data)
    print(f"  4. URL-encoded data: {postdata}")
    
    # Step 2: nonce + postdata
    encoded = (str(data['nonce']) + postdata).encode()
    print(f"  5. Encoded (nonce+postdata): {encoded[:50]}...")
    
    # Step 3: SHA256 hash
    sha256_hash = hashlib.sha256(encoded).digest()
    print(f"  6. SHA256 hash: {base64.b64encode(sha256_hash).decode()[:50]}...")
    
    # Step 4: url_path + sha256
    message = url_path.encode() + sha256_hash
    print(f"  7. Message (path+hash): {len(message)} bytes")
    
    # Step 5: Decode secret
    try:
        decoded_secret = base64.b64decode(secret)
        print(f"  8. Decoded secret: {len(decoded_secret)} bytes")
    except Exception as e:
        print(f"  8. {Fore.RED}ERROR decoding secret: {e}{Style.RESET_ALL}")
        return None
    
    # Step 6: HMAC-SHA512
    mac = hmac.new(decoded_secret, message, hashlib.sha512)
    sig_digest = base64.b64encode(mac.digest())
    signature = sig_digest.decode()
    
    print(f"  9. Final signature: {signature[:50]}...")
    print()
    
    return signature

def test_public_endpoint():
    """Test public endpoint (no auth needed)"""
    print_section("TEST 1: Public Endpoint (No Authentication)")
    
    url = "https://api.kraken.com/0/public/Time"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200 and 'result' in data:
            print(f"{Fore.GREEN}✅ Public API is working!{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Public API failed{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Exception: {e}{Style.RESET_ALL}")
        return False

def test_credentials_format():
    """Test API credentials format"""
    print_section("TEST 2: API Credentials Format Check")
    
    api_key = os.getenv('API_KEY', '')
    api_secret = os.getenv('API_SECRET', '')
    
    print(f"API_KEY length: {len(api_key)}")
    print(f"API_KEY starts with: {api_key[:20] if len(api_key) > 20 else api_key}")
    print()
    print(f"API_SECRET length: {len(api_secret)}")
    print(f"API_SECRET starts with: {api_secret[:20] if len(api_secret) > 20 else api_secret}")
    print()
    
    issues = []
    
    # Check API key format
    if not api_key:
        issues.append("❌ API_KEY is empty")
    elif len(api_key) < 50:
        issues.append("⚠️  API_KEY seems too short (should be 56 chars)")
    elif len(api_key) != 56:
        issues.append(f"⚠️  API_KEY length is {len(api_key)}, expected 56")
    else:
        print(f"{Fore.GREEN}✅ API_KEY length looks correct{Style.RESET_ALL}")
    
    # Check API secret format
    if not api_secret:
        issues.append("❌ API_SECRET is empty")
    elif len(api_secret) < 80:
        issues.append("⚠️  API_SECRET seems too short (should be 88 chars)")
    elif len(api_secret) != 88:
        issues.append(f"⚠️  API_SECRET length is {len(api_secret)}, expected 88")
    else:
        print(f"{Fore.GREEN}✅ API_SECRET length looks correct{Style.RESET_ALL}")
    
    # Try to base64 decode the secret
    try:
        decoded = base64.b64decode(api_secret)
        print(f"{Fore.GREEN}✅ API_SECRET is valid base64 ({len(decoded)} bytes){Style.RESET_ALL}")
    except Exception as e:
        issues.append(f"❌ API_SECRET is not valid base64: {e}")
    
    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")
        return False
    
    return True

def test_private_balance():
    """Test private Balance endpoint"""
    print_section("TEST 3: Private Balance Endpoint (With Authentication)")
    
    api_key = os.getenv('API_KEY', '')
    api_secret = os.getenv('API_SECRET', '')
    
    if not api_key or not api_secret:
        print(f"{Fore.RED}❌ API credentials not found in .env{Style.RESET_ALL}")
        return False
    
    url_path = '/0/private/Balance'
    url = 'https://api.kraken.com' + url_path
    
    # Generate nonce
    nonce = str(int(time.time() * 1000))
    data = {'nonce': nonce}
    
    print(f"URL: {url}")
    print(f"Nonce: {nonce}")
    print()
    
    # Generate signature with debug
    signature = get_signature_debug(url_path, data, api_secret)
    
    if not signature:
        print(f"{Fore.RED}❌ Failed to generate signature{Style.RESET_ALL}")
        return False
    
    # Prepare headers
    headers = {
        'API-Key': api_key,
        'API-Sign': signature,
        'User-Agent': 'Kraken Python API'
    }
    
    print(f"{Fore.YELLOW}Making API Request:{Style.RESET_ALL}")
    print(f"  Headers: API-Key: {api_key[:20]}...")
    print(f"           API-Sign: {signature[:50]}...")
    print(f"  Body (form-data): {urlencode(data)}")
    print()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,  # Send as form data, not JSON!
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            if 'error' in result and result['error']:
                error_msg = result['error']
                print(f"{Fore.RED}❌ Kraken API Error: {error_msg}{Style.RESET_ALL}")
                print()
                print(f"{Fore.YELLOW}Common Solutions:{Style.RESET_ALL}")
                
                if 'EAPI:Invalid key' in str(error_msg):
                    print("  • API key is incorrect or doesn't exist")
                    print("  • Go to: https://www.kraken.com/u/security/api")
                    print("  • Verify the key or create a new one")
                    print("  • Make sure to copy the FULL key (56 characters)")
                
                elif 'EAPI:Bad request' in str(error_msg):
                    print("  • API key and secret don't match")
                    print("  • The secret belongs to a different key")
                    print("  • Delete and recreate BOTH key and secret together")
                
                elif 'EAPI:Invalid signature' in str(error_msg):
                    print("  • Signature generation issue")
                    print("  • API secret might be corrupted")
                    print("  • Try creating a fresh API key")
                
                elif 'EAPI:Invalid nonce' in str(error_msg):
                    print("  • Nonce issue (time synchronization)")
                    print("  • Check your system time is correct")
                
                return False
            
            elif 'result' in result:
                balance = result['result']
                print(f"{Fore.GREEN}✅ API Connection SUCCESSFUL!{Style.RESET_ALL}")
                print()
                print(f"{Fore.CYAN}Your Kraken Balances:{Style.RESET_ALL}")
                if balance:
                    for currency, amount in balance.items():
                        print(f"  {currency}: {amount}")
                else:
                    print(f"  {Fore.YELLOW}(Empty account - deposit funds to trade){Style.RESET_ALL}")
                return True
        
        else:
            print(f"{Fore.RED}❌ HTTP Error {response.status_code}{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Exception: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_signature_methods():
    """Test alternative signature methods in case the main one is wrong"""
    print_section("TEST 4: Alternative Signature Methods")
    
    api_key = os.getenv('API_KEY', '')
    api_secret = os.getenv('API_SECRET', '')
    
    if not api_key or not api_secret:
        print("Skipping (no credentials)")
        return
    
    url_path = '/0/private/Balance'
    nonce = str(int(time.time() * 1000))
    data = {'nonce': nonce}
    
    print("Testing different signature approaches...")
    print()
    
    # Method 1: Current implementation
    print(f"{Fore.YELLOW}Method 1: Standard (nonce + urlencode){Style.RESET_ALL}")
    try:
        postdata = urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = url_path.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(api_secret), message, hashlib.sha512)
        sig1 = base64.b64encode(mac.digest()).decode()
        print(f"  Signature: {sig1[:50]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Method 2: Without URL encoding
    print(f"\n{Fore.YELLOW}Method 2: Without urlencode{Style.RESET_ALL}")
    try:
        postdata_raw = f"nonce={nonce}"
        encoded = postdata_raw.encode()
        message = url_path.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(api_secret), message, hashlib.sha512)
        sig2 = base64.b64encode(mac.digest()).decode()
        print(f"  Signature: {sig2[:50]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()

def main():
    print(f"{Fore.CYAN}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "KRAKEN API DIAGNOSTIC TOOL" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Style.RESET_ALL}")
    
    results = []
    
    # Test 1: Public endpoint
    results.append(("Public API", test_public_endpoint()))
    
    # Test 2: Credentials format
    results.append(("Credentials Format", test_credentials_format()))
    
    # Test 3: Private balance endpoint
    results.append(("Private API (Balance)", test_private_balance()))
    
    # Test 4: Alternative methods
    test_alternative_signature_methods()
    
    # Summary
    print_section("SUMMARY")
    for test_name, passed in results:
        status = f"{Fore.GREEN}✅ PASS" if passed else f"{Fore.RED}❌ FAIL"
        print(f"  {status}{Style.RESET_ALL} - {test_name}")
    
    print()
    
    if all(result[1] for result in results):
        print(f"{Fore.GREEN}🎉 ALL TESTS PASSED! Your Kraken API is working!{Style.RESET_ALL}")
        print()
        print("Next steps:")
        print("  1. Your bot is ready to trade")
        print("  2. Run: python3 live_trade.py")
        print()
        return 0
    else:
        print(f"{Fore.RED}❌ SOME TESTS FAILED{Style.RESET_ALL}")
        print()
        print("Next steps:")
        print("  1. Fix the issues shown above")
        print("  2. Most likely: Create a NEW API key on Kraken")
        print("  3. Go to: https://www.kraken.com/u/security/api")
        print("  4. Copy BOTH the key and secret carefully")
        print("  5. Run this diagnostic again")
        print()
        return 1

if __name__ == "__main__":
    exit(main())
