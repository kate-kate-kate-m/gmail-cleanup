import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

LABELS_TO_NEST = [
    'Boomerang',
    'Boomerang-Outbox',
    'Boomerang-Returned',
    'casa',
    'credit',
    'Deleted Messages',
    'ehcli',
    'fbook',
    'home',
    'house hunt',
    'junkmoney',
    'keep in inbox',
    'loan$',
    'misc',
    'notes',
    'pitt alum',
    'receipts',
    'reference',
    'ru',
    'smartsitting',
    'tc',
    'unroll.me',
    'volunteer',
    'yobs',
]


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
    service = get_service()

    all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_map = {l['name']: l['id'] for l in all_labels}

    # Create "Old" parent label if it doesn't exist
    if 'Old' not in label_map:
        result = service.users().labels().create(userId='me', body={
            'name': 'Old',
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }).execute()
        print("Created 'Old' label")

    # Rename each label to nest it under Old
    moved, skipped = [], []
    for name in LABELS_TO_NEST:
        if name in label_map:
            service.users().labels().patch(
                userId='me',
                id=label_map[name],
                body={'name': f'Old/{name}'}
            ).execute()
            moved.append(name)
        else:
            skipped.append(name)

    print(f"\nMoved {len(moved)} labels under 'Old':")
    for m in moved:
        print(f"  {m} -> Old/{m}")

    if skipped:
        print(f"\nNot found (skipped):")
        for s in skipped:
            print(f"  {s}")


if __name__ == '__main__':
    main()
