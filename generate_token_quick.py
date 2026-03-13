"""
Generate Zerodha Access Token - Simplified version
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from kiteconnect import KiteConnect
import webbrowser
from datetime import datetime
from dotenv import set_key

# Read current credentials
from config.settings import get_settings
settings = get_settings()

API_KEY = settings.ZERODHA_API_KEY
API_SECRET = settings.ZERODHA_API_SECRET

print("=" * 60)
print("🔑 Zerodha Token Generator")
print("=" * 60)
print()
print(f"API Key: {API_KEY[:10]}..." if API_KEY else "API Key: [NOT SET]")
print(f"Time: {datetime.now().strftime('%I:%M %p')}")
print()

# Initialize Kite
kite = KiteConnect(api_key=API_KEY)

# Generate login URL
login_url = kite.login_url()

print("Step 1: Opening browser for Zerodha login...")
print()
print(f"URL: {login_url}")
print()

# Open browser
webbrowser.open(login_url)

print("=" * 60)
print("INSTRUCTIONS:")
print("=" * 60)
print("1. Login with your Zerodha credentials in the browser")
print("2. After login, you'll be redirected to a URL like:")
print("   http://127.0.0.1/?request_token=XXXXX&action=login&status=success")
print()
print("3. Copy the 'request_token' value from that URL")
print("=" * 60)
print()

# Get request token from user
request_token = input("Paste the request_token here: ").strip()

if not request_token:
    print("❌ No token provided!")
    sys.exit(1)

print()
print("Generating access token...")

try:
    # Generate session
    data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]
    
    print()
    print("=" * 60)
    print("✅ SUCCESS!")
    print("=" * 60)
    print()
    print(f"Access Token: {access_token[:20]}..." if len(access_token) > 20 else access_token)
    print(f"User ID: {data.get('user_id', 'N/A')}")
    print()
    
    # Save to .env
    env_path = Path(__file__).parent / ".env"
    
    # Read current .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update lines without adding quotes
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('ZERODHA_REQUEST_TOKEN='):
                f.write(f'ZERODHA_REQUEST_TOKEN={request_token}\n')
            elif line.startswith('ZERODHA_ACCESS_TOKEN='):
               f.write(f'ZERODHA_ACCESS_TOKEN={access_token}\n')
            else:
                f.write(line)
    
    print("✅ Saved to .env file")
    print()
    
    # IMPORTANT: Also update environment variable in current PowerShell session
    # This ensures immediate use without restarting terminal
    import os
    os.environ['ZERODHA_ACCESS_TOKEN'] = access_token
    os.environ['ZERODHA_REQUEST_TOKEN'] = request_token
    print("✅ Updated environment variables in current session")
    print()
    
    print(f"Valid until: 11:59 PM IST ({datetime.now().strftime('%B %d, %Y')})")
    print()
    print("=" * 60)
    print("🚀 Ready to trade!")
    print("=" * 60)
    
    # Test the token
    print()
    print("Testing token...")
    kite.set_access_token(access_token)
    profile = kite.profile()
    print(f"✅ Token verified - User: {profile['user_name']}")
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ Error generating token")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("Please try again or check:")
    print("  - Request token is correct")
    print("  - API secret is correct")
    sys.exit(1)
