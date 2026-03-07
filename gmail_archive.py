#!/usr/bin/env python3
"""
Gmail Archive Script
Creates a "2025 archive" label and moves all inbox emails
older than December 4, 2025 into it.
"""

import time
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

ARCHIVE_LABEL = '2025 archive'
CUTOFF_DATE = '2025/12/04'  # Emails before this date get archived


def authenticate():
    creds = None
    from os.path import exists
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


def archive_old_emails(service, label_id):
    total = 0
    page_token = None
    query = f'in:inbox before:{CUTOFF_DATE}'

    print(f"  Searching for emails before {CUTOFF_DATE}...")

    while True:
        kwargs = {'userId': 'me', 'q': query, 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token

        results = service.users().messages().list(**kwargs).execute()
        messages = results.get('messages', [])

        if not messages:
            break

        ids = [m['id'] for m in messages]
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': ids,
                'addLabelIds': [label_id],
                'removeLabelIds': ['INBOX'],
            }
        ).execute()

        total += len(ids)
        print(f"  Archived {total} emails so far...")

        page_token = results.get('nextPageToken')
        if not page_token:
            break
        time.sleep(0.3)

    return total


def main():
    print("\n=== Gmail Archive Script ===")
    print(f"Archiving all inbox emails before {CUTOFF_DATE} into '{ARCHIVE_LABEL}'\n")

    print("Connecting to Gmail...")
    service = authenticate()
    print("Connected!\n")

    print("Step 1: Creating label...")
    label_id = create_label(service, ARCHIVE_LABEL)

    print("\nStep 2: Moving old emails to archive (this may take a while)...")
    total = archive_old_emails(service, label_id)

    print(f"\n=== DONE ===")
    print(f"Moved {total} emails to '{ARCHIVE_LABEL}'.")
    print("Your inbox now only contains emails from December 4, 2025 onwards.")


if __name__ == '__main__':
    main()
