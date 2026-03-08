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
DELIVER_HOUR_ET = 16  # 4pm ET


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


def get_or_create_label(service, name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'] == name:
            return label['id']
    label = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelHide', 'messageListVisibility': 'hide'}
    ).execute()
    return label['id']


def main():
    # Only deliver at/after 4pm ET
    now_et = datetime.datetime.now(ZoneInfo('America/New_York'))
    if now_et.hour < DELIVER_HOUR_ET:
        print(f"Not yet 4pm ET (currently {now_et.strftime('%I:%M %p')} ET) — skipping")
        return

    service = get_service()

    # Get or create the tracking label
    delivered_label_id = get_or_create_label(service, 'substack-delivered')

    # Find Substack emails from the last 24 hours that haven't been delivered yet
    messages = []
    result = service.users().messages().list(
        userId='me', q='label:Substack -in:inbox -label:substack-delivered newer_than:1d', maxResults=500
    ).execute()
    messages.extend(result.get('messages', []))
    while 'nextPageToken' in result:
        result = service.users().messages().list(
            userId='me', q='label:Substack -in:inbox -label:substack-delivered newer_than:1d',
            maxResults=500, pageToken=result['nextPageToken']
        ).execute()
        messages.extend(result.get('messages', []))

    if not messages:
        print("No Substack emails to deliver")
        return

    for msg in messages:
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'addLabelIds': ['INBOX', delivered_label_id]}
        ).execute()

    print(f"Delivered {len(messages)} Substack email(s) to inbox")


if __name__ == '__main__':
    main()
