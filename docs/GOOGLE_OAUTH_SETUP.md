# Google OAuth Setup Guide for ResearchAI

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it: `ResearchAI` (or your preferred name)
4. Click **Create**

## Step 2: Enable Google Sign-In API

1. Go to **APIs & Services** → **Library**
2. Search for **"Google Identity"** or **"Google Sign-In"**
3. Click on **Google Identity Services**
4. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (for public users) or **Internal** (for organization only)
3. Click **Create**
4. Fill in the required fields:
   - **App name:** `ResearchAI`
   - **User support email:** Your email
   - **Developer contact email:** Your email
5. Click **Save and Continue**
6. Skip **Scopes** for now (click Save and Continue)
7. Add **Test users** if using External (your email)
8. Click **Save and Continue**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `ResearchAI Web Client`
5. **Authorized JavaScript origins:**
   ```
   http://localhost:3000
   http://localhost:3001
   http://127.0.0.1:3000
   ```
6. **Authorized redirect URIs:**
   ```
   http://localhost:3000
   http://localhost:3000/api/auth/callback/google
   http://localhost:3001
   ```
7. Click **Create**

## Step 5: Copy Your Credentials

After creating, you'll see:
- **Client ID:** `xxxxx.apps.googleusercontent.com`
- **Client Secret:** `GOCSPX-xxxxx`

## Step 6: Update Your Environment Files

### Frontend (.env.local)
```bash
# frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
```

### Backend (.env)
```bash
# .env (in project root)
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## Step 7: Restart Your Servers

```powershell
# Stop both servers (Ctrl+C)

# Terminal 1 - Backend
cd C:\Users\ashar\Documents\rpa_claude_desktop
uvicorn src.api.main:app --reload --port 8001

# Terminal 2 - Frontend
cd C:\Users\ashar\Documents\rpa_claude_desktop\frontend
npm run dev
```

## Step 8: Test Google Sign-In

1. Open http://localhost:3000/signup
2. Click **"Sign up with Google"**
3. Select your Google account
4. You should be redirected to the dashboard

## Troubleshooting

### "Google Sign-In is loading" error
- Wait a few seconds for the Google SDK to load
- Refresh the page and try again

### "Invalid client_id" error
- Double-check your Client ID in `.env.local`
- Make sure there are no extra spaces

### "redirect_uri_mismatch" error
- Add your current URL to the Authorized JavaScript origins
- Add your current URL to the Authorized redirect URIs

### CORS errors
- Make sure the backend CORS is configured for your frontend URL
- Check that both servers are running

## Production Setup

For production, add your production domain to:
1. Authorized JavaScript origins: `https://yourdomain.com`
2. Authorized redirect URIs: `https://yourdomain.com`

Then update your production environment variables accordingly.
