````markdown name=README.md url=https://github.com/tricontinentconstructionchem-lang/trichem/blob/main/README.md
# TriContinent Construction Chemicals — Gmail Agent

An automated AI-powered email response system for managing buyer inquiries about construction chemical admixtures (superplasticizers, air entrainers, etc.).

The agent uses **Claude 3.5 Sonnet** to generate professional responses and **Gmail API** to send them automatically.

---

## 🚀 Quick Start

### 1. **One-time Setup**

#### Step A: Create Google Cloud Project & Enable Gmail API

1. Go to https://console.cloud.google.com/
2. Create new project: **TriContinent Gmail Agent**
3. Go to **APIs & Services** → **Library**
4. Search and enable **Gmail API**
5. Go to **OAuth consent screen**:
   - Select **External** → **Create**
   - App name: `TriContinent Agent`
   - Emails: `info@tricontinentconstructionchem.com`
   - Continue → **Add Scopes** → Add these 3:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.modify`
   - Add yourself as Test User

6. Go to **Credentials** → **Create Credentials** → **OAuth Client ID**
   - Application type: **Desktop app**
   - Download JSON as `credentials.json`

#### Step B: Get Anthropic API Key

1. Go to https://console.anthropic.com/keys
2. Create API key, copy it

#### Step C: Clone & Setup Repo

```bash
git clone https://github.com/tricontinentconstructionchem-lang/trichem.git
cd trichem

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Place credentials
# → Copy credentials.json to this folder

# Configure environment
cp .env.example .env
# Edit .env and add:
#   ANTHROPIC_API_KEY=sk-ant-xxxx...
#   GMAIL_FROM=info@tricontinentconstructionchem.com
```

---

## 📧 How It Works

```
┌─────────────────────────────────────┐
│  Buyer sends inquiry to Gmail       │
│  (e.g., requesting PCE quote)       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Agent Backend monitors inbox       │
│  (every 15 min via GitHub Actions)  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Claude AI generates response       │
│  (professional, customized)         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Agent sends reply via Gmail        │
│  (using Gmail API)                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Buyer receives AI-generated reply  │
│  (within minutes)                   │
└─────────────────────────────────────┘
```

---

## 🏃 Running Locally

### Test the System

```bash
# Terminal 1: Send a test buyer inquiry
python tricontinent_agent_test.py

# Terminal 2: Run the agent (waits 30s for reply)
python tricontinent_agent_backend.py
```

**Expected output from agent:**
```
================================
   TRICONTINENT — GMAIL AGENT BACKEND
================================

🔐 Authenticating with Gmail...
✅ Authenticated

📥 Fetching unread threads...
   Found 1 unread thread(s)

📨 Processing thread: 18ab1d2c4f5e6a7b
   From: emeka@lagosreadymix.com
   Subject: [AGENT TEST] Superplasticizer Quote Request
   🤖 Generating AI response...
   📤 Sending reply to emeka@lagosreadymix.com...
✅ Reply sent (Message ID: 18ab1d2c4f5e6a7c)

================================
   AGENT SUMMARY
================================
  Processed threads: 1
  Replies sent:      1
  Total processed:   1
  Last run:          2026-04-24T12:15:30.123456
================================
```

---

## ⚙️ Configuration Files

### `.env` (Local)
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx...
GMAIL_FROM=info@tricontinentconstructionchem.com
POLL_INTERVAL_SECONDS=60
MAX_THREADS_PER_RUN=10
```

### `credentials.json` (Google OAuth)
Download from Google Cloud Console OAuth credentials page.
**Keep this SECRET — don't commit to Git.**

### `token.json` (Auto-generated)
Created after first run. Contains Gmail API access token.
**Keep this SECRET — don't commit to Git.**

---

## 🤖 GitHub Actions Setup

The repo includes two automated workflows:

### 1. **Weekly Test** (every Monday at 9 AM UTC)
- Sends a test buyer inquiry
- Verifies agent can respond
- Useful for health checks

### 2. **Continuous Agent** (every 15 minutes)
- Monitors inbox for real inquiries
- Generates and sends replies
- Tracks processed threads

#### To Enable Workflows:

1. Go to repo **Settings** → **Secrets and variables** → **Actions**
2. Add these **Repository Secrets**:

   | Secret | Value | Example |
   |--------|-------|---------|
   | `ANTHROPIC_API_KEY` | Your Claude API key | `sk-ant-abc123...` |
   | `GMAIL_CREDENTIALS` | Base64-encoded `credentials.json` | See below |
   | `GMAIL_FROM` | Your Gmail address | `info@tricontinentconstructionchem.com` |

#### How to encode `credentials.json` to base64:

**On Mac/Linux:**
```bash
cat credentials.json | base64
```

**On Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("credentials.json"))
```

Then paste the output as `GMAIL_CREDENTIALS` secret.

---

## 📊 Agent Features

✅ **Automatic inquiry detection** — Monitors unread inbox for new emails  
✅ **AI-powered responses** — Uses Claude to generate professional, contextual replies  
✅ **Thread tracking** — Avoids duplicate replies using `processed_threads.json`  
✅ **Error handling** — Gracefully handles API failures  
✅ **Gmail integration** — Sends via Gmail API with proper formatting  
✅ **State persistence** — Remembers which threads have been replied to  
✅ **Logging** — Detailed output for troubleshooting  

---

## 🔍 Troubleshooting

### "Cannot find credentials.json"
- Download `credentials.json` from Google Cloud Console
- Place it in the root folder of this repo
- Make sure `.gitignore` prevents accidental commits

### "ANTHROPIC_API_KEY not set"
- Create `.env` file in repo root
- Add: `ANTHROPIC_API_KEY=sk-ant-xxxxx...`
- Restart your terminal

### "Gmail API auth failed"
- Delete `token.json`
- Re-run the script to trigger browser login
- Make sure you log in with the correct Gmail account

### "No replies being sent"
- Check Gmail inbox — inquiry email may not have arrived
- Verify agent backend is running: `python tricontinent_agent_backend.py`
- Check `processed_threads.json` to see what threads were processed

### "GitHub Actions workflows not running"
- Go to **Actions** tab, check for workflow failures
- Verify all **Secrets** are set correctly
- Check `credentials.json` is properly base64-encoded

---

## 📁 File Structure

```
trichem/
├── tricontinent_agent_test.py       # Test script (sends inquiry)
├── tricontinent_agent_backend.py    # Main agent (generates replies)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Ignore secrets
├── README.md                        # This file
├── credentials.json                 # (NOT in Git - keep secret!)
├── token.json                       # (NOT in Git - auto-generated)
├── processed_threads.json           # (Tracks processed emails)
└── .github/workflows/
    ├── gmail-agent-test.yml         # Weekly test workflow
    └── gmail-agent-backend.yml      # Continuous agent workflow
```

---

## 🎯 Example Inquiry & Response

### Incoming Email:
```
From: emeka@lagosreadymix.com
Subject: Superplasticizer Quote Request

Hello TriContinent Team,

I am reaching out on behalf of Lagos Readymix Concrete Ltd.
We are looking to source high-performance PCE superplasticizer 
for our concrete batching plants in Lagos and Abuja.

Requirements:
- Product: PCE Superplasticizer (ASTM C494 Type F)
- Quantity: 5 MT/month (trial: 1 MT)
- Delivery: Apapa Port, Lagos
- Timeline: 45 days

Could you provide pricing, specs, and lead time?

Best regards,
Emeka Okafor
Lagos Readymix Concrete Ltd.
```

### Agent-Generated Reply:
```
From: info@tricontinentconstructionchem.com
Subject: Re: Superplasticizer Quote Request

Dear Emeka,

Thank you for reaching out to TriContinent Construction Chemicals.

We're pleased to learn about your interest in our PCE superplasticizer 
for your batching operations in Lagos and Abuja. We have extensive 
experience supplying premium admixtures to concrete producers across 
West Africa.

For your 1 MT trial order of PCE (ASTM C494 Type F equivalent):
- We can accommodate delivery to Apapa Port within 30-35 days
- Our standard MOQ is 500 kg (well below your trial requirement)
- Technical datasheet and current FOB pricing attached

Next steps:
1. Review the attached specifications
2. Confirm trial quantity and delivery date
3. We'll prepare a formal quotation

Looking forward to establishing a partnership.

Best regards,
TriContinent Sales Team
info@tricontinentconstructionchem.com
+234 801 234 5678
```

---

## 🚀 Deployment Options

### Option 1: GitHub Actions (Recommended)
- **Cost:** Free (up to 2,000 minutes/month)
- **Reliability:** ✅ Highly reliable
- **Setup:** 10 minutes (add secrets)
- **Runs:** Every 15 minutes automatically

### Option 2: Local Cron Job
```bash
# Add to crontab (runs every 15 min):
*/15 * * * * cd /path/to/trichem && python tricontinent_agent_backend.py >> agent.log 2>&1
```

### Option 3: Cloud Server (EC2, DigitalOcean, etc.)
- Deploy repo to server
- Install dependencies
- Run as systemd service or PM2 daemon

### Option 4: Cloud Functions (AWS Lambda, Google Cloud Functions)
- Use serverless if you want minimal overhead
- Schedule with CloudWatch/Cloud Scheduler

---

## 📞 Support

For issues or questions:
- Check the **Troubleshooting** section above
- Review workflow logs in **Actions** tab
- Check Gmail inbox manually at https://mail.google.com
- Verify `processed_threads.json` for state

---

## 📝 License

TriContinent Construction Chemicals — Internal Use Only

---

**Last Updated:** 2026-04-24  
**Status:** ✅ Production Ready
````
