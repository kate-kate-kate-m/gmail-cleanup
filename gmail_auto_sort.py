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
    'westelm.com',
    'lululemon.com',
    'beistravel.com',
    'ruggable.com',
    'playasociety.com',
    'mthdbyus.com',
    'afterpay.com',
    'shopifyemail.com',
    'nike.com',
    'shefitapparel.com',
    'shop.affirm.com',
    'bazaarvoice-cgc.com',
    'narvar.com',
    'meine-studios.com',
    'partnernotification.capitalone.com',
    'mmlafleur.com',
    'shopfavoritedaughter.com',
    'sevlaser.com',
    'cieleathletics.com',
    'f45training.com',
    'stubhub.com',
    'medallia.com',
    'loft.com',
    'soma.com',
    'sojournpottery.com',
    'zeelool.com',
    'bradsdeals.com',
    'eloquii.com',
    'adidas.com',
    'soldout.nyc',
    'heyhanni.com',
    'slicelife.com',
    'credobeauty.com',
    'tnuck.com',
    'fanaticscommerce.com',
    'asos.com',
    'catbirdnyc.com',
    'nomasei.com',
    'strapsicle.com',
    'newyorkornowhere.com',
    'etsy.com',
    'chewy.com',
    'dickssportinggoods.com',
    'shop.app',
    'returntokora.com',
    'ekster.com',
    'gorjana.com',
    'castleflexx.com',
    'plainjanenewyork.com',
    'greatjonesgoods.com',
    'bartonperreira.com',
    'getcanopy.co',
    'fiveirongolf.com',
    'sollishealth.com',
    'parsleyhealth.com',
    'purebarre.com',
    'salt-escapes.com',
    'elfster.com',
    'ihg.com',
    'sonesta.com',
    'guestreservations.com',
    'creditkarma.com',
    'citicards@info15.citi.com',
    'thankyou.citi.com',
]

POLITICAL_DOMAINS = [
    'passmedicareforall.org',
    'boldpac.com',
    'patryanforcongress.com',
    'ginafortexas.com',
    'kathyhochul.com',
    'dnc.org',
    'bendthearc.us',
    'votesaveamerica.com',
    'ncdp.org',
]

NEWSLETTER_DOMAINS = [
    'readtangle.com',
    'livewellbehappy.com',
    'healthycoachhub.com',
    'relentlessmethod.com',
    'benbruno.com',
    'crooked.com',
    'ideabrowser.com',
    'stockmarkethour.com',
    'beehiiv.com',
    'peterattiamd.com',
    'authormaxmonroe.com',
    'luma-mail.com',
    'createcultivate.com',
    'goodreads.com',
    'insightfulword.com',
    'goodword.com',
    'tobemagnetic.com',
]


GENERAL_NEWSLETTER_DOMAINS = [
    'weather.com',
    'moneywitch.com',
    'gallup.com',
    'gabbybernstein.com',
    'janellehardy.com',
    'kmcgheecoaching.com',
    'ifttt.com',
    'chiefofstaff.network',
    'getwingapp.com',
    'edgilitytalent.com',
    'nrgconsultinggroup.org',
    'inclusv.com',
    'nychousingconnect@hpd.nyc.gov',
    'michiganhillel@umich.edu',
]

SPORTS_DOMAINS = [
    'newyorkcityruns.com',
    'usalacrosse.com',
    'premierlacrosseleague.com',
    'tempobasketball.com',
    'powermonkeyfitness.com',
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
    political_label_id = get_or_create_label(service, '2026 Political')

    # Move Substack emails out of inbox into holding folder
    # Exclude emails already labeled Substack — those have been delivered and should stay in inbox
    newsletter_from = ' '.join(f'from:({d})' for d in NEWSLETTER_DOMAINS)
    substack_query = f'in:inbox {{from:(substack.com) {newsletter_from}}} -label:Substack'
    substack_msgs = get_messages(service, substack_query)
    if substack_msgs:
        move_messages(service, substack_msgs, [substack_label_id], ['INBOX'])
        print(f"Moved {len(substack_msgs)} Substack email(s) to holding folder")
    else:
        print("No new Substack emails in inbox")

    # Move retailer emails out of inbox into 2026 Shopping
    retailer_query = 'in:inbox {' + ' '.join(f'from:({d})' for d in RETAILER_DOMAINS) + '}'
    retailer_msgs = get_messages(service, retailer_query)
    if retailer_msgs:
        move_messages(service, retailer_msgs, [shopping_label_id], ['INBOX'])
        print(f"Moved {len(retailer_msgs)} retailer email(s) to 2026 Shopping")
    else:
        print("No new retailer emails in inbox")

    # Move political fundraising emails out of inbox into 2026 Political
    political_query = 'in:inbox {' + ' '.join(f'from:({d})' for d in POLITICAL_DOMAINS) + '}'
    political_msgs = get_messages(service, political_query)
    if political_msgs:
        move_messages(service, political_msgs, [political_label_id], ['INBOX'])
        print(f"Moved {len(political_msgs)} political email(s) to 2026 Political")
    else:
        print("No new political emails in inbox")

    # General newsletters and community mail: archive to 2026 Newsletters (not delivered like Substack)
    news_label_id = get_or_create_label(service, '2026 Newsletters')
    news_query = 'in:inbox {' + ' '.join(f'from:({d})' for d in GENERAL_NEWSLETTER_DOMAINS) + '}'
    news_msgs = get_messages(service, news_query)
    if news_msgs:
        move_messages(service, news_msgs, [news_label_id], ['INBOX'])
        print(f"Moved {len(news_msgs)} newsletter email(s) to 2026 Newsletters")
    else:
        print("No new general newsletter emails in inbox")

    # Sports and fitness marketing: archive to 2026/Sports
    sports_label_id = get_or_create_label(service, '2026/Sports')
    sports_query = 'in:inbox {' + ' '.join(f'from:({d})' for d in SPORTS_DOMAINS) + '}'
    sports_msgs = get_messages(service, sports_query)
    if sports_msgs:
        move_messages(service, sports_msgs, [sports_label_id], ['INBOX'])
        print(f"Moved {len(sports_msgs)} sports email(s) to 2026/Sports")
    else:
        print("No new sports emails in inbox")


if __name__ == '__main__':
    main()
