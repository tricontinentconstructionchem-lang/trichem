"""
=============================================================================
TRICONTINENT CONSTRUCTION CHEMICALS — GMAIL AGENT BACKEND
=============================================================================

This script monitors the Gmail inbox for buyer inquiries and generates
AI-powered responses using Claude 3.5 Sonnet.

SETUP:
  1. pip install -r requirements.txt
  2. Place credentials.json in repo root
  3. Set ANTHROPIC_API_KEY in .env or environment
  4. Run: python tricontinent_agent_backend.py

DEPLOYMENT:
  - Local: cron job every 15 minutes
  - GitHub Actions: Built-in workflow (see .github/workflows/gmail-agent-backend.yml)
  - Cloud: AWS Lambda, Google Cloud Functions, or similar

=============================================================================
"""

import os
import json
import time
import base64
from datetime import datetime
from pathlib import Path

# Google Auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Anthropic
from anthropic import Anthropic

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── CONFIG ────────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

FROM_EMAIL           = os.getenv("GMAIL_FROM", "info@tricontinentconstructionchem.com")
CREDENTIALS_FILE     = "credentials.json"
TOKEN_FILE           = "token.json"
PROCESSED_THREADS    = "processed_threads.json"
POLL_INTERVAL_SECS   = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
MAX_THREADS_PER_RUN  = int(os.getenv("MAX_THREADS_PER_RUN", "10"))
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY")

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional sales and technical support agent for TriContinent Construction Chemicals.

You handle inquiries about construction chemical admixtures including:
- PCE (Polycarboxylate Ether) Superplasticizers
- Air Entrainers
- Water Reducers
- Retarders
- Accelerators
- Other concrete admixtures

Your responses should:
1. Be professional, courteous, and helpful
2. Address the specific needs mentioned in the inquiry
3. Provide technical information when appropriate
4. Offer to provide datasheets, samples, or quotes
5. Include contact information for follow-up
6. Keep responses concise (2-3 paragraphs max)
7. Sign off as "TriContinent Sales Team"

If the inquiry is about products outside your scope, politely redirect to info@tricontinentconstructionchem.com."""

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
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)

# ── STATE MANAGEMENT ──────────────────────────────────────────────────────────

def load_processed_threads():
    """Load set of already-processed thread IDs."""
    if os.path.exists(PROCESSED_THREADS):
        try:
            with open(PROCESSED_THREADS, "r") as f:
                data = json.load(f)
                return set(data.get("thread_ids", []))
        except json.JSONDecodeError:
            return set()
    return set()

def save_processed_threads(thread_ids):
    """Save processed thread IDs to avoid duplicates."""
    with open(PROCESSED_THREADS, "w") as f:
        json.dump({
            "thread_ids": list(thread_ids),
            "last_updated": datetime.now().isoformat()
        }, f, indent=2)

# ── FETCH UNREAD THREADS ──────────────────────────────────────────────────────

def fetch_unread_threads(service, max_results=MAX_THREADS_PER_RUN):
    """Fetch unread threads from inbox."""
    try:
        results = service.users().threads().list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
            format="full"
        ).execute()

        return results.get("threads", [])

    except HttpError as e:
        print(f"⚠️ Error fetching threads: {e}")
        return []

# ── EXTRACT MESSAGE CONTENT ───────────────────────────────────────────────────

def extract_message_content(message):
    """Extract sender, subject, and body from a Gmail message."""
    headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}

    sender  = headers.get("From", "Unknown")
    subject = headers.get("Subject", "(no subject)")
    
    # Decode body
    body = ""
    payload = message["payload"]

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

    return sender, subject, body

# ── GENERATE AI RESPONSE ──────────────────────────────────────────────────────

def generate_response(inquiry_body):
    """Generate AI response using Claude."""
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY not set. Skipping AI response generation.")
        return None

    try:
        client = Anthropic()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Please respond to this inquiry:\n\n{inquiry_body}"}
            ]
        )

        return message.content[0].text

    except Exception as e:
        print(f"⚠️ Error generating response: {e}")
        return None

# ── SEND REPLY ────────────────────────────────────────────────────────────────

def send_reply(service, to_email, subject, body):
    """Send a reply via Gmail."""
    # Add "Re:" if not already present
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"

    message = MIMEMultipart()
    message["to"]      = to_email
    message["from"]    = FROM_EMAIL
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return sent["id"]

    except HttpError as e:
        print(f"❌ Failed to send email: {e}")
        return None

# ── MARK THREAD AS READ ───────────────────────────────────────────────────────

def mark_thread_as_read(service, thread_id):
    """Mark thread as read after processing."""
    try:
        service.users().threads().modify(
            userId="me",
            id=thread_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except HttpError as e:
        print(f"⚠️ Could not mark thread as read: {e}")

# ── PROCESS THREAD ────────────────────────────────────────────────────────────

def process_thread(service, thread_id, processed_threads):
    """Process a single thread: read, generate response, send reply."""
    
    # Skip if already processed
    if thread_id in processed_threads:
        return False

    try:
        # Get thread
        thread = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full"
        ).execute()

        messages = thread.get("messages", [])
        if not messages:
            return False

        # Get the first message (original inquiry)
        original = messages[0]
        sender, subject, body = extract_message_content(original)

        print(f"\n📨 Processing thread: {thread_id}")
        print(f"   From: {sender}")
        print(f"   Subject: {subject}")

        # Generate response
        print(f"   🤖 Generating AI response...")
        response = generate_response(body)

        if not response:
            print(f"   ⚠️ Could not generate response. Skipping.")
            return False

        # Send reply
        print(f"   📤 Sending reply...")
        message_id = send_reply(service, sender, subject, response)

        if message_id:
            print(f"   ✅ Reply sent (Message ID: {message_id})")
            mark_thread_as_read(service, thread_id)
            return True
        else:
            print(f"   ❌ Failed to send reply.")
            return False

    except Exception as e:
        print(f"   ❌ Error processing thread: {e}")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("   TRICONTINENT — GMAIL AGENT BACKEND")
    print("="*60)

    # Load processed threads
    processed_threads = load_processed_threads()
    print(f"\n📊 State: {len(processed_threads)} threads already processed")

    # Authenticate
    print("\n🔐 Authenticating with Gmail...")
    service = authenticate()
    print("✅ Authenticated")

    # Fetch unread threads
    print(f"\n📥 Fetching unread threads...")
    threads = fetch_unread_threads(service)
    print(f"   Found {len(threads)} unread thread(s)")

    if not threads:
        print("\n   No unread threads. Exiting.")
        print("="*60 + "\n")
        return

    # Process each thread
    processed_count = 0
    for thread in threads:
        if process_thread(service, thread["id"], processed_threads):
            processed_threads.add(thread["id"])
            processed_count += 1

    # Save state
    save_processed_threads(processed_threads)

    # Summary
    print("\n" + "="*60)
    print("   AGENT SUMMARY")
    print("="*60)
    print(f"  Processed threads: {processed_count}")
    print(f"  Replies sent:      {processed_count}")
    print(f"  Total processed:   {len(processed_threads)}")
    print(f"  Last run:          {datetime.now().isoformat()}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
