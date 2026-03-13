"""
Zerodha Kite Connect - Token Generation Utility

This script helps you generate an access token for Zerodha Kite API.
It will:
1. Generate a login URL
2. Start a local server to capture the callback
3. Exchange request token for access token
4. Save the token to your .env file

Run this script once to get your access token.
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

API_KEY = os.getenv('ZERODHA_API_KEY')
API_SECRET = os.getenv('ZERODHA_API_SECRET')
REDIRECT_URL = "http://localhost:9088/callback"

# Global variable to store request token
request_token = None
server_instance = None

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from Zerodha redirect"""
        global request_token
        
        # Parse the URL and extract request_token
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'request_token' in query_params:
            request_token = query_params['request_token'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Kite Token Generated</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Success!</h1>
                <p>Authentication successful. Request token captured.</p>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
            # Shutdown server after capturing token
            print(f"\n✓ Request token captured: {request_token[:20]}...")
            
        else:
            # Error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">✗ Error</h1>
                <p>No request token found in callback.</p>
                <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def validate_credentials():
    """Validate API credentials are present"""
    if not API_KEY or not API_SECRET:
        print("❌ Error: Zerodha API credentials not found!")
        print("\nPlease add the following to your .env file:")
        print("ZERODHA_API_KEY=your_api_key")
        print("ZERODHA_API_SECRET=your_api_secret")
        sys.exit(1)
    
    print("✓ API credentials loaded")
    print(f"  API Key: {API_KEY[:10]}...")

def start_callback_server():
    """Start HTTP server to capture callback"""
    global server_instance
    
    print(f"\n⏳ Starting callback server on {REDIRECT_URL}...")
    
    server_address = ('localhost', 9088)
    server_instance = HTTPServer(server_address, CallbackHandler)
    
    print("✓ Server started. Waiting for callback...")
    
    # Handle single request (the callback)
    server_instance.handle_request()

def generate_access_token():
    """Generate access token from request token"""
    global request_token
    
    if not request_token:
        print("❌ Error: No request token available")
        return None
    
    print("\n⏳ Generating access token...")
    
    try:
        kite = KiteConnect(api_key=API_KEY)
        
        # Generate session
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        
        access_token = data["access_token"]
        user_id = data["user_id"]
        
        print("✓ Access token generated successfully!")
        print(f"  User ID: {user_id}")
        print(f"  Access Token: {access_token[:20]}...")
        
        return access_token, user_id
        
    except Exception as e:
        print(f"❌ Error generating access token: {e}")
        return None

def save_to_env(access_token, user_id):
    """Save access token to .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    
    print(f"\n⏳ Saving credentials to {env_path}...")
    
    try:
        # Update .env file
        set_key(env_path, 'ZERODHA_ACCESS_TOKEN', access_token)
        set_key(env_path, 'ZERODHA_USER_ID', user_id)
        
        print("✓ Credentials saved to .env file")
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\nYour Kite API is now configured and ready to use.")
        print("\nNext steps:")
        print("1. Run: python services/market_data/ingestion_pipeline.py")
        print("2. Start the trading system: python start.py")
        print("\nNote: Access tokens are valid for 1 day. Re-run this script")
        print("      tomorrow if you need a fresh token.")
        
    except Exception as e:
        print(f"❌ Error saving to .env: {e}")
        print(f"\nPlease manually add these to your .env file:")
        print(f"ZERODHA_ACCESS_TOKEN={access_token[:20]}...")
        print(f"ZERODHA_USER_ID={user_id}")
        print("\n⚠️  Copy the full token from the success message above")

def main():
    """Main execution flow"""
    print("="*60)
    print("  Zerodha Kite Connect - Token Generator")
    print("="*60)
    
    # Step 1: Validate credentials
    validate_credentials()
    
    # Step 2: Generate login URL
    kite = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    
    print(f"\n📋 Step 1: Login to Zerodha")
    print("="*60)
    print("\nYour browser will open with the Zerodha login page.")
    print("After logging in, you'll be redirected back automatically.")
    print("\nIf the browser doesn't open, copy this URL:")
    print(f"\n{login_url}\n")
    
    input("Press ENTER to open the login page...")
    
    # Open browser
    webbrowser.open(login_url)
    
    print("\n📋 Step 2: Waiting for authentication...")
    print("="*60)
    
    # Step 3: Start callback server
    start_callback_server()
    
    # Step 4: Generate access token
    if request_token:
        print("\n📋 Step 3: Generating access token...")
        print("="*60)
        
        result = generate_access_token()
        
        if result:
            access_token, user_id = result
            save_to_env(access_token, user_id)
        else:
            print("\n❌ Failed to generate access token")
            sys.exit(1)
    else:
        print("\n❌ Failed to capture request token")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
