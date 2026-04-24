"""
=============================================================================
TRICONTINENT CONSTRUCTION CHEMICALS — GMAIL AGENT TEST SCRIPT
=============================================================================

SETUP STEPS (Do these ONCE before running the script)
------------------------------------------------------

STEP 1: Create a Google Cloud Project
  1. Go to https://console.cloud.google.com/
  2. Click the project dropdown (top left) → "New Project"
  3. Name it: TriContinent Gmail Agent
  4. Click Create

STEP 2: Enable Gmail API
  1. Go to APIs & Services → Library
  2. Search for "Gmail API"
  3. Click it → Click "Enable"

STEP 3: Configure OAuth Consent Screen
  1. Go to APIs & Services → OAuth consent screen
  2. Select "External" → Click Create
  3. Fill in:
       App name: TriContinent Agent Test
       User support email: info@tricontinentconstructionchem.com
       Developer contact email: info@tricontinentconstructionchem.com
  4. Click Save and Continue
  5. Under Scopes → click "Add or Remove Scopes"
  6. Add these scopes:
       https://www.googleapis.com/auth/gmail.send
       https://www.googleapis.com/auth/gmail.readonly
       https://www.googleapis.com/auth/gmail.modify
  7. Save and Continue → Add yourself as a Test User → Save

STEP 4: Create OAuth Credentials
  1. Go to APIs & Services → Credentials
  2. Click "Create Credentials" → OAuth Client ID
  3. Application type: Desktop App
  4. Name: TriContinent Gmail Client
  5. Click Create
  6. Click "Download JSON"
  7. Save the file as: credentials.json
  8. Move credentials.json into the SAME folder as this script

STEP 5: Install Dependencies
  Run this in your terminal:
  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic

STEP 6: Run the Script
  python tricontinent_agent_test.py

  → First run: A browser window will open asking you to log in with your
    Google account. Log in with the TriContinent Gmail account.
  → A token.json file will be saved. Future runs won't need browser login.

=============================================================================
"""

import os
import base64
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Google Auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── CONFIG ────────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

FROM_EMAIL    = "info@tricontinentconstructionchem.com"   # Your TriContinent Gmail
TO_EMAIL      = "info@tricontinentconstructionchem.com"   # Send test TO same inbox
CREDENTIALS   = "credentials.json"                        # Downloaded from Google Cloud
TOKEN_FILE    = "token.json"                              # Auto-created after first login
POLL_SECONDS  = 30                                        # How long to wait for response
POLL_INTERVAL = 5                                         # Check every N seconds

# ── AUTH ──────────────────────────────────────────────────────────────────────

def authenticate():
    """Authenticate with Gmail API. Opens browser on first run."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for Google login...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)

# ── BUILD TEST EMAIL ──────────────────────────────────────────────────────────

def build_test_email():
    """Build a realistic buyer inquiry to test the agent."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    subject = f"[AGENT TEST] Superplasticizer Quote Request — {timestamp}"

    body = f"""
Hello TriContinent Team,

I am reaching out on behalf of Lagos Readymix Concrete Ltd.
We are looking to source high-performance PCE superplasticizer admixture 
for our concrete batching plants in Lagos and Abuja.

Our requirements:
- Product: Polycarboxylate Ether (PCE) Superplasticizer
- Grade: High water reduction (ASTM C494 Type F or equivalent)
- Quantity: 5 metric tons per month (trial order: 1 MT)
- Delivery: Lagos, Nigeria (Apapa Port)
- Timeline: Within 45 days

Could you please provide:
1. Product datasheet and technical specifications
2. FOB price per metric ton
3. Minimum order quantity
4. Estimated lead time from your supplier

We look forward to establishing a long-term supply relationship.

Best regards,
Emeka Okafor
Procurement Manager
Lagos Readymix Concrete Ltd.
+234 801 234 5678

---
[AUTOMATED TEST MESSAGE — Sent at {timestamp}]
"""

    return subject, body

# ── SEND EMAIL ────────────────────────────────────────────────────────────────

def send_test_email(service):
    """Send the test email and return the message ID."""
    subject, body = build_test_email()

    message = MIMEMultipart()
    message["to"]      = TO_EMAIL
    message["from"]    = FROM_EMAIL
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        print(f"\n{'='*60}")
        print("📤 TEST EMAIL SENT")
        print(f"{'='*60}")
        print(f"  To:        {TO_EMAIL}")
        print(f"  Subject:   {subject}")
        print(f"  Message ID: {sent['id']}")
        print(f"  Thread ID:  {sent['threadId']}")
        print(f"{'='*60}\n")

        return sent["id"], sent["threadId"]

    except HttpError as e:
        print(f"❌ Failed to send email: {e}")
        raise

# ── POLL FOR AGENT REPLY ──────────────────────────────────────────────────────

def poll_for_reply(service, thread_id, wait_seconds=POLL_SECONDS):
    """Poll the inbox for an agent reply on the same thread."""
    print(f"⏳ Polling for agent reply (up to {wait_seconds}s)...\n")
    start = time.time()
    checked = 0

    while time.time() - start < wait_seconds:
        checked += 1
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] Checking thread {thread_id}...", end="\r")

        try:
            thread = service.users().threads().get(
                userId="me",
                id=thread_id,
                format="full"
            ).execute()

            messages = thread.get("messages", [])

            if len(messages) > 1:
                # There's a reply beyond the original sent message
                print(f"\n\n✅ AGENT REPLY DETECTED! ({len(messages)-1} reply(s))\n")
                for i, msg in enumerate(messages[1:], 1):
                    display_message(msg, i)
                return True

        except HttpError as e:
            print(f"\n⚠️ Error polling thread: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"\n\n⏰ No reply received within {wait_seconds} seconds.")
    print("   → Agent may not be running, or reply takes longer.")
    print("   → Check your inbox manually at mail.google.com\n")
    return False

# ── DISPLAY MESSAGE ───────────────────────────────────────────────────────────

def display_message(msg, index=1):
    """Parse and display a Gmail message cleanly."""
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    subject = headers.get("Subject", "(no subject)")
    sender  = headers.get("From",    "(unknown sender)")
    date    = headers.get("Date",    "(unknown date)")

    # Decode body
    body = ""
    payload = msg["payload"]

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
    elif "body" in payload:
        data = payload["body"].get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    print(f"{'─'*60}")
    print(f"📨 REPLY #{index}")
    print(f"{'─'*60}")
    print(f"  From:    {sender}")
    print(f"  Subject: {subject}")
    print(f"  Date:    {date}")
    print(f"{'─'*60}")
    print(f"\n{body.strip()}\n")
    print(f"{'─'*60}\n")

# ── LIST RECENT INBOX ─────────────────────────────────────────────────────────

def list_recent_inbox(service, max_results=5):
    """Show the 5 most recent inbox messages for reference."""
    print("\n📥 RECENT INBOX (last 5 messages):")
    print(f"{'─'*60}")

    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            print("  Inbox is empty.")
            return

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            print(f"  📧 {headers.get('Subject', '(no subject)')}")
            print(f"     From: {headers.get('From', '?')} | {headers.get('Date', '?')}")
            print()

    except HttpError as e:
        print(f"  ⚠️ Could not fetch inbox: {e}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("   TRICONTINENT — GMAIL AGENT TEST")
    print("="*60)

    # 1. Authenticate
    print("\n🔐 Authenticating with Gmail API...")
    service = authenticate()
    print("✅ Authenticated successfully.\n")

    # 2. Show inbox snapshot
    list_recent_inbox(service)

    # 3. Send test email
    print("\n📤 Sending test buyer inquiry email...")
    message_id, thread_id = send_test_email(service)

    # 4. Poll for agent reply
    reply_found = poll_for_reply(service, thread_id, wait_seconds=POLL_SECONDS)

    # 5. Summary
    print("\n" + "="*60)
    print("   TEST SUMMARY")
    print("="*60)
    print(f"  Message sent:    ✅ (ID: {message_id})")
    print(f"  Agent replied:   {'✅ YES' if reply_found else '❌ NOT YET'}")
    print(f"  Thread ID:       {thread_id}")
    print(f"  Check Gmail at:  https://mail.google.com")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
