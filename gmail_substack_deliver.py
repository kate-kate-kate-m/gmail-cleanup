import os
import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')
FLAG_FILE = os.path.join(os.path.dirname(__file__), 'last_delivered.txt')
DELIVER_HOUR_ET = 16  # 4pm ET


def already_delivered_today():
    if not os.path.exists(FLAG_FILE):
        return False
    with open(FLAG_FILE) as f:
        return f.read().strip() == datetime.date.today().isoformat()


def mark_delivered():
    with open(FLAG_FILE, 'w') as f:
        f.write(datetime.date.today().isoformat())


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def main():
    # Only deliver at/after 4pm ET, and only once per day
    now_et = datetime.datetime.now(ZoneInfo('America/New_York'))
    if now_et.hour < DELIVER_HOUR_ET:
        print(f"Not yet 4pm ET (currently {now_et.strftime('%I:%M %p')} ET) — skipping")
        return
    if already_delivered_today():
        print("Already delivered today — skipping")
        return

    service = get_service()

    # Find the Substack label
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    substack_label_id = next((l['id'] for l in labels if l['name'] == 'Substack'), None)

    if not substack_label_id:
        print("No Substack label found — nothing to deliver")
        return

    # Find messages in Substack holding folder from the last 24 hours (not yet in inbox)
    messages = []
    result = service.users().messages().list(
        userId='me', q='label:Substack -in:inbox newer_than:1d', maxResults=500
    ).execute()
    messages.extend(result.get('messages', []))
    while 'nextPageToken' in result:
        result = service.users().messages().list(
            userId='me', q='label:Substack -in:inbox newer_than:1d',
            maxResults=500, pageToken=result['nextPageToken']
        ).execute()
        messages.extend(result.get('messages', []))

    if not messages:
        print("No Substack emails to deliver")
        mark_delivered()
        return

    for msg in messages:
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'addLabelIds': ['INBOX']}
        ).execute()

    mark_delivered()
    print(f"Delivered {len(messages)} Substack email(s) to inbox")


if __name__ == '__main__':
    main()
