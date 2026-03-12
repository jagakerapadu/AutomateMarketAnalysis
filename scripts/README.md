# Utility Scripts

## Generate Kite Access Token

### Purpose
Zerodha Kite Connect requires an access token for API authentication. This token needs to be generated daily through OAuth flow.

### How to Use

1. **Ensure your .env has API credentials:**
   ```env
   ZERODHA_API_KEY=your_api_key_from_kite_developers
   ZERODHA_API_SECRET=your_api_secret_from_kite_developers
   ```

2. **Run the token generator:**
   ```powershell
   python scripts\generate_kite_token.py
   ```

3. **Follow the steps:**
   - Press ENTER when prompted
   - Your browser will open Zerodha login page
   - Login with your credentials
   - Complete 2FA if enabled
   - You'll be redirected to `http://localhost:9088/callback`
   - The script will automatically capture the token

4. **Token saved automatically:**
   The script will add these to your `.env` file:
   ```env
   ZERODHA_ACCESS_TOKEN=your_generated_token
   ZERODHA_USER_ID=your_zerodha_user_id
   ```

### Important Notes

- **Token Validity**: Access tokens are valid for **1 day only**
- **Daily Refresh**: You need to run this script every day before market hours
- **No Manual Copying**: The token is automatically saved to `.env`
- **Callback URL**: Must match what you set in Kite Developer Console

### Setting up Kite Developer Account

1. Go to https://developers.kite.trade/
2. Create an app
3. Set redirect URL to: `http://localhost:9088/callback`
4. Note down your API Key and API Secret
5. Add them to `.env` file

### Troubleshooting

**Error: Port 9088 already in use**
- Close any process using port 9088
- Or change the port in the script

**Error: Invalid callback URL**
- Ensure `http://localhost:9088/callback` is set in your Kite app settings
- The URL must match exactly (including protocol and port)

**Token not saved to .env**
- Check file permissions
- Manually copy the printed token to `.env` file

**Browser doesn't open**
- Manually copy the login URL printed in terminal
- Paste it in your browser
- Complete the login process

### Automation (Optional)

To avoid running this daily, you can:
1. Create a scheduled task to run this script at 7:00 AM
2. Or integrate TOTP-based auto-login (advanced)

### Example Output

```
============================================================
  Zerodha Kite Connect - Token Generator
============================================================
✓ API credentials loaded
  API Key: abcd1234...

📋 Step 1: Login to Zerodha
============================================================

Press ENTER to open the login page...

📋 Step 2: Waiting for authentication...
============================================================
⏳ Starting callback server on http://localhost:9088/callback...
✓ Server started. Waiting for callback...

✓ Request token captured: xyz789abc...

📋 Step 3: Generating access token...
============================================================
⏳ Generating access token...
✓ Access token generated successfully!
  User ID: AB1234
  Access Token: 1234567890abcdef...

⏳ Saving credentials to .env...
✓ Credentials saved to .env file

============================================================
✅ SETUP COMPLETE!
============================================================

Your Kite API is now configured and ready to use.
```

### Next Steps

After generating the token:
1. Run: `python services\market_data\ingestion_pipeline.py`
2. Start trading system: `python start.py`
