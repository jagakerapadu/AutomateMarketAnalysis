# Fix GitHub Push Permission Error

## Problem
```
Permission denied to Jegathees272
fatal: unable to access: The requested URL returned error: 403
```

Git is using wrong GitHub credentials. Need to authenticate as `jagakerapadu`.

---

## Solution 1: Using Personal Access Token (Recommended)

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `AutomateMarketAnalysis`
4. Set expiration: 90 days (or No expiration)
5. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - ✅ **workflow** (if you use GitHub Actions)
6. Click **"Generate token"**
7. **COPY THE TOKEN** (you'll only see it once!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Clear Old Credentials

```powershell
# Remove cached credentials
git credential reject
# When prompted, paste this and press Enter twice:
# protocol=https
# host=github.com
```

### Step 3: Push with Token

```powershell
# Method A: Push with token in URL (one-time)
git push https://YOUR_TOKEN@github.com/jagakerapadu/AutomateMarketAnalysis.git main
```

**Or store credentials:**

```powershell
# Method B: Configure credential storage (recommended)
git config --global credential.helper wincred

# Then push (it will prompt for username/password):
git push origin main

# Enter:
#   Username: jagakerapadu
#   Password: YOUR_PERSONAL_ACCESS_TOKEN (paste the ghp_xxx token)
```

---

## Solution 2: Using SSH (Alternative)

### Step 1: Generate SSH Key

```powershell
# Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Enter passphrase (optional)
```

### Step 2: Add SSH Key to GitHub

```powershell
# Copy public key to clipboard
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard

# Go to: https://github.com/settings/keys
# Click "New SSH key"
# Title: "Trading System PC"
# Paste key and save
```

### Step 3: Change Remote to SSH

```powershell
# Change remote URL to SSH
git remote set-url origin git@github.com:jagakerapadu/AutomateMarketAnalysis.git

# Test connection
ssh -T git@github.com
# Should say: "Hi jagakerapadu! You've successfully authenticated"

# Push
git push origin main
```

---

## Solution 3: Quick Fix with Username Override

```powershell
# Set repository-specific username
git config user.name "jagakerapadu"
git config user.email "your_email@example.com"

# Remove credential helper temporarily
git config --unset credential.helper

# Push (will prompt for credentials)
git push origin main
```

---

## Verification Commands

```powershell
# Check current git config
git config --list | Select-String "user|credential|remote"

# Check what will be pushed
git log origin/main..main --oneline

# Check remote URL
git remote -v
```

---

## After Successful Push

Verify on GitHub:
1. Go to: https://github.com/jagakerapadu/AutomateMarketAnalysis
2. You should see your latest commit
3. Check that `.env` is NOT visible (should be ignored)

---

## Troubleshooting

### If still getting 403:
```powershell
# Clear all credential caches
cmdkey /list | Select-String "git" | ForEach-Object { cmdkey /delete:$_.ToString().Split()[1] }

# Or manually:
# Control Panel → Credential Manager → Windows Credentials
# Remove any "git:https://github.com" entries
```

### If wrong email/name in commits:
```powershell
# Fix last commit author
git commit --amend --author="jagakerapadu <your_email@example.com>" --no-edit

# Force push (only if you haven't shared the branch)
git push origin main --force
```

---

## Security Note

⚠️ **Never share your Personal Access Token!**
- Treat it like a password
- Store it securely (e.g., password manager)
- If exposed, immediately revoke it on GitHub and create a new one

✅ Your `.env` file with real credentials is protected and won't be pushed!
