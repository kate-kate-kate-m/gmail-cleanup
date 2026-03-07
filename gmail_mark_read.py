#!/usr/bin/env python3
"""
Mark all inbox emails as read, move them to "2026 cleanup", and empty the inbox.
"""

import time
from os.path import exists
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic',
]
TOKEN_FILE = 'token.json'
CREDS_FILE = 'credentials.json'
CLEANUP_LABEL = '2026 cleanup'


def authenticate():
    creds = None
    if exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def create_label(service, name):
    existing = service.users().labels().list(userId='me').execute()
    for label in existing.get('labels', []):
        if label['name'] == name:
            print(f"  Label '{name}' already exists.")
            return label['id']
    label = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    print(f"  Created label '{name}'.")
    return label['id']


def process_inbox(service, label_id):
    total = 0
    page_token = None

    while True:
        kwargs = {'userId': 'me', 'q': 'in:inbox', 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token

        results = service.users().messages().list(**kwargs).execute()
        messages = results.get('messages', [])

        if not messages:
            break

        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [m['id'] for m in messages],
                'addLabelIds': [label_id],
                'removeLabelIds': ['INBOX', 'UNREAD'],
            }
        ).execute()

        total += len(messages)
        print(f"  Processed {total} emails...")

        page_token = results.get('nextPageToken')
        if not page_token:
            break
        time.sleep(0.2)

    return total


def main():
    print("\n=== Inbox Zero Script ===")
    print(f"Marking all inbox emails as read and moving to '{CLEANUP_LABEL}'\n")

    print("Connecting to Gmail...")
    service = authenticate()
    print("Connected!\n")

    print("Step 1: Creating label...")
    label_id = create_label(service, CLEANUP_LABEL)

    print("\nStep 2: Moving all inbox emails to '2026 cleanup' and marking as read...")
    total = process_inbox(service, label_id)

    print(f"\n=== DONE ===")
    print(f"Moved {total} emails to '{CLEANUP_LABEL}'.")
    print("Your inbox is now empty.")


if __name__ == '__main__':
    main()
