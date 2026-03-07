import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

RETAILER_DOMAINS = [
    'amazon.com',
    'aptdeco.com',
    'wanderingbearcoffee.com',
    'arborteas.com',
    'andar.com',
    'litfarms.com',
    'm2performancenutrition.com',
    'libro.fm',
    'grammarly.com',
    'canva.com',
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


def get_or_create_label(service, name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'] == name:
            return label['id']
    result = service.users().labels().create(userId='me', body={
        'name': name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }).execute()
    return result['id']


def get_messages(service, query):
    messages = []
    result = service.users().messages().list(userId='me', q=query, maxResults=500).execute()
    messages.extend(result.get('messages', []))
    while 'nextPageToken' in result:
        result = service.users().messages().list(
            userId='me', q=query, maxResults=500, pageToken=result['nextPageToken']
        ).execute()
        messages.extend(result.get('messages', []))
    return messages


def move_messages(service, messages, add_labels, remove_labels):
    for msg in messages:
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'addLabelIds': add_labels, 'removeLabelIds': remove_labels}
        ).execute()


def main():
    service = get_service()

    substack_label_id = get_or_create_label(service, 'Substack')
    shopping_label_id = get_or_create_label(service, '2026 Shopping')

    # Move Substack emails out of inbox into holding folder
    # Exclude emails already labeled Substack — those have been delivered and should stay in inbox
    substack_msgs = get_messages(service, 'in:inbox from:(@substack.com) -label:Substack')
    if substack_msgs:
        move_messages(service, substack_msgs, [substack_label_id], ['INBOX'])
        print(f"Moved {len(substack_msgs)} Substack email(s) to holding folder")
    else:
        print("No new Substack emails in inbox")

    # Move retailer emails out of inbox into 2026 Shopping
    retailer_query = 'in:inbox {' + ' '.join(f'from:(@{d})' for d in RETAILER_DOMAINS) + '}'
    retailer_msgs = get_messages(service, retailer_query)
    if retailer_msgs:
        move_messages(service, retailer_msgs, [shopping_label_id], ['INBOX'])
        print(f"Moved {len(retailer_msgs)} retailer email(s) to 2026 Shopping")
    else:
        print("No new retailer emails in inbox")


if __name__ == '__main__':
    main()
