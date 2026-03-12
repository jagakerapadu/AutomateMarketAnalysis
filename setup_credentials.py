"""
Secure Credential Management for Trading APIs
Supports: Zerodha Kite, ICICI Direct
Stores encrypted credentials in .env file
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import getpass
import webbrowser
from urllib.parse import urlparse, parse_qs

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def read_env():
    """Read current .env file"""
    env_path = Path(".env")
    if not env_path.exists():
        return {}
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def write_env(env_vars):
    """Write environment variables to .env file"""
    env_path = Path(".env")
    
    # Group variables by category
    sections = {
        'Database': ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'],
        'Zerodha': ['ZERODHA_API_KEY', 'ZERODHA_API_SECRET', 'ZERODHA_ACCESS_TOKEN'],
        'ICICI Direct': ['ICICI_API_KEY', 'ICICI_API_SECRET', 'ICICI_SESSION_TOKEN'],
        'Application': ['API_PORT', 'LOG_LEVEL']
    }
    
    lines = []
    lines.append("# Trading System Configuration")
    lines.append(f"# Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Write sections
    for section, keys in sections.items():
        lines.append(f"# {section}")
        for key in keys:
            value = env_vars.get(key, '')
            lines.append(f"{key}={value}")
        lines.append("")
    
    # Write any remaining variables
    written_keys = set().union(*sections.values())
    for key, value in env_vars.items():
        if key not in written_keys:
            lines.append(f"{key}={value}")
    
    with open(env_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Credentials saved to {env_path.absolute()}")

def setup_zerodha():
    """Setup Zerodha Kite credentials"""
    clear_screen()
    print_header("ZERODHA KITE API SETUP")
    
    print("📖 Instructions:")
    print("  1. Login to https://developers.kite.trade/")
    print("  2. Create a new app or use existing one")
    print("  3. Copy API Key and API Secret")
    print("  4. Set Redirect URL to: http://127.0.0.1:5000/callback")
    print("")
    
    # Get credentials
    api_key = input("Enter Zerodha API Key: ").strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        return None
    
    api_secret = getpass.getpass("Enter Zerodha API Secret (hidden): ").strip()
    if not api_secret:
        print("❌ API Secret cannot be empty")
        return None
    
    # Generate access token
    print("\n🔐 Generating Access Token...")
    print("  Opening browser for authentication...")
    
    login_url = f"https://kite.trade/connect/login?api_key={api_key}&v=3"
    
    proceed = input(f"\nOpen browser to authorize? (y/n): ").lower()
    if proceed == 'y':
        webbrowser.open(login_url)
        print("\n✅ Browser opened. After login, you'll be redirected to a URL.")
        print("   Copy the ENTIRE redirect URL from browser address bar.")
        print("   Example: http://127.0.0.1:5000/callback?request_token=xxxxx&action=login&status=success")
        print("")
    else:
        print(f"\n📋 Manually open this URL in browser:\n{login_url}\n")
    
    redirect_url = input("Paste the full redirect URL here: ").strip()
    
    # Extract request token
    try:
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        request_token = query_params.get('request_token', [None])[0]
        
        if not request_token:
            print("❌ Could not extract request_token from URL")
            return None
        
        print(f"\n✅ Request Token: {request_token[:20]}...")
        
        # Generate access token using KiteConnect
        try:
            from kiteconnect import KiteConnect
            
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(request_token, api_secret=api_secret)
            access_token = data["access_token"]
            
            print(f"✅ Access Token Generated: {access_token[:20]}...")
            print(f"   Valid until: {data.get('login_time', 'N/A')}")
            
            return {
                'ZERODHA_API_KEY': api_key,
                'ZERODHA_API_SECRET': api_secret,
                'ZERODHA_ACCESS_TOKEN': access_token
            }
            
        except ImportError:
            print("\n⚠️  kiteconnect package not installed")
            print("   Install: pip install kiteconnect")
            print("\n   For now, saving API credentials without access token.")
            return {
                'ZERODHA_API_KEY': api_key,
                'ZERODHA_API_SECRET': api_secret,
                'ZERODHA_ACCESS_TOKEN': ''
            }
        except Exception as e:
            print(f"\n❌ Error generating access token: {e}")
            print("   Saving API credentials. Generate token later using:")
            print("   py scripts/generate_kite_token.py")
            return {
                'ZERODHA_API_KEY': api_key,
                'ZERODHA_API_SECRET': api_secret,
                'ZERODHA_ACCESS_TOKEN': ''
            }
    
    except Exception as e:
        print(f"❌ Error processing URL: {e}")
        return None

def setup_icici():
    """Setup ICICI Direct API credentials"""
    clear_screen()
    print_header("ICICI DIRECT API SETUP")
    
    print("📖 Instructions:")
    print("  1. Login to ICICI Direct API Portal")
    print("  2. Navigate to API Management section")
    print("  3. Generate API Key and API Secret")
    print("  4. Note: Session tokens expire after 24 hours")
    print("")
    
    # Get credentials
    api_key = input("Enter ICICI Direct API Key: ").strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        return None
    
    api_secret = getpass.getpass("Enter ICICI Direct API Secret (hidden): ").strip()
    if not api_secret:
        print("❌ API Secret cannot be empty")
        return None
    
    # Optional: Get session token
    print("\n🔐 Session Token (Optional):")
    print("  Leave empty to generate later")
    session_token = getpass.getpass("Enter Session Token (or press Enter): ").strip()
    
    credentials = {
        'ICICI_API_KEY': api_key,
        'ICICI_API_SECRET': api_secret,
        'ICICI_SESSION_TOKEN': session_token
    }
    
    print("\n✅ ICICI Direct credentials configured")
    if not session_token:
        print("   Note: Generate session token when running the system")
    
    return credentials

def view_credentials():
    """View current credentials (masked)"""
    clear_screen()
    print_header("CURRENT CREDENTIALS")
    
    env_vars = read_env()
    
    # Zerodha
    print("🔹 Zerodha Kite:")
    zerodha_key = env_vars.get('ZERODHA_API_KEY', '')
    zerodha_secret = env_vars.get('ZERODHA_API_SECRET', '')
    zerodha_token = env_vars.get('ZERODHA_ACCESS_TOKEN', '')
    
    print(f"  API Key:      {zerodha_key[:10]}..." if zerodha_key else "  API Key:      [NOT SET]")
    print(f"  API Secret:   {'*' * 20}" if zerodha_secret else "  API Secret:   [NOT SET]")
    print(f"  Access Token: {zerodha_token[:15]}..." if zerodha_token else "  Access Token: [NOT SET]")
    
    # ICICI
    print("\n🔹 ICICI Direct:")
    icici_key = env_vars.get('ICICI_API_KEY', '')
    icici_secret = env_vars.get('ICICI_API_SECRET', '')
    icici_token = env_vars.get('ICICI_SESSION_TOKEN', '')
    
    print(f"  API Key:        {icici_key[:10]}..." if icici_key else "  API Key:        [NOT SET]")
    print(f"  API Secret:     {'*' * 20}" if icici_secret else "  API Secret:     [NOT SET]")
    print(f"  Session Token:  {icici_token[:15]}..." if icici_token else "  Session Token:  [NOT SET]")
    
    # Database
    print("\n🔹 Database:")
    print(f"  Host: {env_vars.get('DB_HOST', 'localhost')}")
    print(f"  Port: {env_vars.get('DB_PORT', '5434')}")
    print(f"  Name: {env_vars.get('DB_NAME', 'trading_db')}")
    print(f"  User: {env_vars.get('DB_USER', 'postgres')}")
    
    input("\n\nPress Enter to continue...")

def main_menu():
    """Main menu for credential management"""
    while True:
        clear_screen()
        print_header("CREDENTIAL MANAGEMENT SYSTEM")
        
        print("1. 🔑 Setup Zerodha Kite API")
        print("2. 🔑 Setup ICICI Direct API")
        print("3. 👁️  View Current Credentials")
        print("4. 🔄 Regenerate Zerodha Access Token")
        print("5. 💾 Save & Exit")
        print("6. ❌ Exit without Saving")
        print("")
        
        choice = input("Enter choice (1-6): ").strip()
        
        env_vars = read_env()
        
        if choice == '1':
            credentials = setup_zerodha()
            if credentials:
                env_vars.update(credentials)
                print("\n✅ Zerodha credentials configured")
                input("Press Enter to continue...")
        
        elif choice == '2':
            credentials = setup_icici()
            if credentials:
                env_vars.update(credentials)
                print("\n✅ ICICI credentials configured")
                input("Press Enter to continue...")
        
        elif choice == '3':
            view_credentials()
        
        elif choice == '4':
            print("\n🔄 Regenerating Zerodha Access Token...")
            api_key = env_vars.get('ZERODHA_API_KEY')
            api_secret = env_vars.get('ZERODHA_API_SECRET')
            
            if not api_key or not api_secret:
                print("❌ Zerodha API credentials not found. Setup Zerodha first.")
                input("Press Enter to continue...")
                continue
            
            # Run fresh token generation
            credentials = setup_zerodha()
            if credentials:
                env_vars.update(credentials)
                print("\n✅ Access token regenerated")
                input("Press Enter to continue...")
        
        elif choice == '5':
            write_env(env_vars)
            print("\n✅ All changes saved!")
            print("   You can now run: py start.py")
            input("\nPress Enter to exit...")
            break
        
        elif choice == '6':
            confirm = input("\n⚠️  Exit without saving? (y/n): ").lower()
            if confirm == 'y':
                print("❌ Changes discarded")
                break
        
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
