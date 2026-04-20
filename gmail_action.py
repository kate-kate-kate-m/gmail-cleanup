#!/usr/bin/env python3
"""
Gmail Action Script - Kate's Inbox Cleanup
1. Unsubscribes from marketing senders
2. Archives existing emails from those senders
3. Creates LinkedIn Jobs, Sports, and 2026 Receipts labels
4. Sets up filters so future emails skip inbox and go to labels
5. Moves existing relevant emails into labels
"""

import os
import json
import re
import time
import urllib.request
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

# ==============================================================================
# SENDERS TO UNSUBSCRIBE FROM
# ==============================================================================
UNSUBSCRIBE_SENDERS = [
    # --- Batch 1 (already processed) ---
    'info@n.skinstore.com',
    'hello@thesill.com',
    'sperry@mailing.sperry.com',
    'teamzoom@e.zoom.us',
    'webinars@e.zoom.us',
    'newsletter@hhm.healthyhabitatmarket.com',
    'newsletter@blog.innovationsandhealth.com',
    'dig@emails.thanx.com',
    'joecoffee@emails.thanx.com',
    'noreply@hello.klarna.com',
    'no-reply@messages.doordash.com',
    'no-reply@marketing.lyftmail.com',
    'no-reply@f45training.com',
    'no-reply@m.ouraring.com',
    'email@hello.babbel.com',
    'no-reply@gowatch.nbc.com',
    'advertise-noreply@global.metamail.com',
    'no-reply@channels.primevideo.com',
    'no-reply@notifications.whoop.com',
    'donotreply@e.zeelool.com',
    'marketing@newsletter.eatokra.com',
    'info@dailyprovisionsnyc.com',
    'emails@thanx.com',
    'hello@onepercentimprovements.convertkit.com',
    'no-reply@mail.goodreads.com',
    'editors-noreply@linkedin.com',
    'messages-noreply@linkedin.com',
    # --- Batch 2 ---
    'noreply@email.streeteasy.com',
    'noreply@streeteasy.com',
    'noreply@goodamerican.com',
    'noreply@a.email.hbr.org',
    'noreply@email.hbr.org',
    'noreply@m.klarna.com',
    'noreply@e.klarna.com',
    'noreply@redditmail.com',
    'no-reply@is.email.nextdoor.com',
    'no-reply@rs.email.nextdoor.com',
    'noreply@ms.email.nextdoor.com',
    'donotreply@e.society6.com',
    'donotreply@t.society6.com',
    'newsletter@theskint.com',
    'noreply@r.groupon.com',
    'newsletter@shopfavoritedaughter.com',
    'no-reply@email.peacocktv.com',
    'donotreply@afterpay.com',
    'newsletter@cravingsbychrissyteigen.com',
    'newsletter@citywinery.com',
    'newsletter@blavity.com',
    'newsletter@mail.blavity.com',
    'noreply@skims.com',
    'noreply@e.lifetime.life',
    'noreply@t.lifetime.life',
    'noreply@emails.lifetime.life',
    'advertise-noreply@support.facebook.com',
    'noreply@business-updates.facebook.com',
    'no-reply@yelp.com',
    'no-reply@mail.yelp.com',
    'noreply@mail.amcentertainment.com',
    'noreply@email.amctheatres.com',
    'donotreply@shondaland.com',
    'noreply@hyrox.com',
    'no-reply@marketing.espnmail.com',
    'espnpromotions@espnmail.com',
    'newsletter@illesteva.com',
    'newsletter@service.tiktok.com',
    'no-reply@primevideo.com',
    'donotreply@23andme.com',
    'noreply@mail.23andme.com',
    'newsletter@reply.ticketmaster.com',
    'noreply@send.candid.org',
    'noreply@candid.org',
    # --- Batch 3 ---
    'no-reply@mail.joinfound.com',           # Found app
    'newsletter@nysun.com',                  # NY Sun
    'newsletter@email.pvolve.com',           # Pvolve
    'noreply@employer-network.com',          # Employer Network spam
    'updates@truemed.com',                   # Truemed
    'noreply@shop.app',                      # Shop/Shopify
    'newsletter@bergesinstitute.com',        # Berges Institute
    'no-reply@notifications.arketa.co',      # The joy project
    'arketa-noreply@arketa.co',              # The joy project (alt)
    'pollers@thepandaresearchedition.com',   # PandaEdition
    'member@yourpandadept.com',              # Panda Dept
    'news@pandaresearch-survs.com',          # PandaSurveys
    'no-reply@marketing.gogreenwood.com',    # Greenwood
    'newsletter@thehomeedit.com',            # The Home Edit
    'newsletter@canadapooch.com',            # Canada Pooch
    'noreply@canadapooch.com',               # Canada Pooch (alt)
    'noreply@shopthenovogratz.com',          # The Novogratz
    'noreply@thenovogratz.com',              # The Novogratz (alt)
    'donotreply@loseit.com',                 # Lose It!
    'no-reply@compass.com',                  # Compass real estate
    'noreply@e.lululemon.com',               # lululemon
    'newsletter@oppositewall.com',           # Opposite Wall
    'noreply@emails.castlery.com',           # Castlery
    'no-reply@politicsny.com',               # Politics NY
    'no-reply@stumblemail.com',              # StumbleUpon (defunct)
    'noreply@moviepass.com',                 # MoviePass (defunct)
    'no-reply@email.nbc.com',               # NBC
    'newsletter@cruz.senate.gov',            # Ted Cruz
    'noreply@regenics.com',                  # Regenics
    'staff@dlcc.org',                        # DLCC
    'NoReply@email.bestegg.com',             # Best Egg
    'no-reply@marketing.zerolongevity.com',  # Zero fasting
    'no-reply@marketing.zerofasting.com',    # Zero fasting (alt)
    'newsletter@dosomething.org',            # DoSomething
    'newsletter@metrowize.com',              # MetroWize
    'newsletter@bdwayinfo.com',              # Broadway Direct
    'noreply@summersalt.com',                # Summersalt
    'newsletter@mail.monicavinader.com',     # Monica Vinader
    'noreply@smc.waxcenter.com',             # European Wax Center
    'no-reply@newsletter.tp-link.com',       # TP-Link
    'tplinkus@newsletter.tp-link.com',       # TP-Link (alt)
    'donotreply@ismellgreat.com',            # i smell great
    'no-reply@passionplanner.com',           # Passion Planner
    'noreply@medium.com',                    # Medium
    'no-reply@postmates.com',                # Postmates (defunct)
    'newsletter@official.nikestrength.com',  # Nike Strength
    'wordsofwomennewsletter@ghost.io',       # Words of Women
    'no-reply@joindeleteme.com',             # DeleteMe newsletter
    'deleteme+newsletter@joindeleteme.com',  # DeleteMe newsletter (alt)
    'noreply@fentybeauty.com',               # Fenty Beauty
    'no-reply@mail.kissusa.com',             # KISS cosmetics
    'noreply@e.dyson.com',                   # Dyson
    'noreply@email.usopen.org',              # US Open shop
    'warnerbros@updates.warnerbros.com',     # Warner Bros
    'noreply@unikwax.com',                   # Uni K Wax
    'no-reply@flywheelsports.com',           # Flywheel Sports
    'hello@news.bodyboss.com',               # BodyBoss
    'noreply@tnuck.com',                     # Tuckernuck
    'noreply@kaiyo.com',                     # Kaiyo
    'email.replies@newsletter.mobilize.us',  # Mobilize political
    'noreply@mobilize.us',                   # Mobilize (alt)
    'communications@maps.org',               # MAPS Newsletter
    'NewYorker@newsletter.newyorker.com',    # The New Yorker
    'newsletter@adamgrant.net',              # Adam Grant
    'newsletter@hechingerreport.org',        # Hechinger Report
    'noreply@gm.chief.com',                  # Chief in Brief
    'no-reply@m.sofi.org',                   # SoFi marketing
    'no-reply@o.sofi.org',                   # SoFi marketing (alt)
    'no-reply@r.sofi.com',                   # SoFi marketing (alt)
    'noreply@results.equinox.com',           # Equinox marketing
    'newsletter@womenshealthmag.com',        # Women's Health
    'no-reply@theskimm.com',                 # The Skimm
    'hrweek@e.shrm.org',                     # SHRM
    'hrmagazine@e.shrm.org',                 # SHRM magazine
    'noreply@robinhood.com',                 # Robinhood Snacks newsletter
    'noreply@wayfair.com',                   # Wayfair
    'noreply@paintnite.com',                 # Paint Nite
    'donotreply@showclix.com',               # ShowClix
    'noreply@f.anthropologie.com',           # Anthropologie
    'noreply@zenoti.com',                    # Zenoti spa marketing
    'no-reply@email.signalaward.com',        # Signal Awards
    'newsletter@email-nmss.org',             # National MS Society
    'no-reply@emailoutreach.wharton.upenn.edu', # Wharton MBA
    'noreply@swingleft.org',                 # Swing Left
    'no-reply@amazonmusic.com',              # Amazon Music marketing
    'no-reply@msg.amazonmusic.com',          # Amazon Music (alt)
    'no-reply@announce.fiverr.com',          # Fiverr marketing
    'donotreply@bestyetmarket.com',          # Best Market
    'no-reply@corkcicle.com',               # Corkcicle
    'info@naca.org',                         # NACA Newsletter
    'no-reply@tryfi.com',                    # Fi Smart Collar marketing (keep transactional)
    'noreply@robinhood.com',                 # Robinhood newsletter
    'noreply@prezi.com',                     # Prezi
    'noreply@upwork.com',                    # Upwork marketing
    'no-reply@announce.fiverr.com',          # Fiverr
    'donotreply@upwork.com',                 # Upwork (alt)
    # --- Batch 4 ---
    'no-reply@substack.com',                 # Substack
    'donotreply@match.indeed.com',           # Indeed job alerts
    'no-reply@loox.io',                      # This Months Craft
    'noreply@reminder.eventbrite.com',       # Eventbrite
    'no-reply+16044926@toast-restaurants.com', # Leyla restaurant
    'cscm-newsletter@mail.beehiiv.com',      # Center for Spine Care + Mobility
    'no-reply+430af0c1@toast-restaurants.com', # Petee's Pie
    'noreply@projectrepat.com',              # Project Repat
    'noreply@h5.hilton.com',                 # Hilton Honors
    'noreply@e.stmarysclothingdrive.com',    # St. Mary's Clothing Drive
    'no-reply+8f04252d@toast-restaurants.com', # Bodrum restaurant
    # --- Batch 5 ---
    'hello@timeleft.com',                    # Timeleft
    'hello@send.checkmatetoday.com',         # Favorite Daughter x Checkmate
    'info@update.rackroomshoes.com',         # Rack Room Shoes
    'hello@votefwd.org',                     # Vote Forward
    'news@email.webbyawards.com',            # The Webby Awards
    'hello@831stories.com',                  # 831 Stories
    'no-reply@cuddlduds.com',                # Cuddl Duds
    'info@marketing.mlbemail.com',           # MLB Insider
    'hello@news.na.hyrox.com',               # HYROX World USA
    'info@email-nmss.org',                   # National MS Society
    'info@jewishaction.us',                  # Bend the Arc: Jewish Action
    'marketing@evebyboz.com',               # Eve by Boz
    'hello@hello-sunshine.com',              # Hello Sunshine
    'info@filmpittsburgh.org',               # Film Pittsburgh
    'hello@knkg.com',                        # KNKG
    'americanexpress@member.americanexpress.com', # Amex Offers
    'info@eml.upstart.com',                  # Upstart
    'info@hudsonsailing.org',                # Hudson River Community Sailing
    'info@arborteas.com',                    # Arbor Teas
    'info@email.signalaward.com',            # Signal Awards News
    'info@sheshouldrun.org',                 # She Should Run
    'formfitnessbk@info-formfitnessbk.com', # Form Fitness
    'hello@libro.fm',                        # Libro.fm
    'info@morancompany.com',                 # The Moran Company
    'hello@marisafalcon.com',               # Marisa Falcon
    'simong@goldenpenwriting.info',          # Simon Golden
    'info@jfrej.org',                        # JFREJ
    'no-reply@youtube.com',                  # YouTube TV
]

# ==============================================================================
# SENDERS TO DELETE AND MARK AS SPAM
# ==============================================================================
DELETE_AND_SPAM_SENDERS = [
    'noreply@notify.thinkific.com',          # Conspiring Women
    'noreply.invitations@trustpilotmail.com', # Nurx review request
]

# ==============================================================================
# SENDERS TO DELETE ONLY (not spam)
# ==============================================================================
DELETE_ONLY_SENDERS = [
    'no-reply@ashbyhq.com',                  # Campus Hiring Team
]

# ==============================================================================
# LABEL CONFIGURATIONS
# ==============================================================================
LABEL_CONFIGS = {
    '2026/LinkedIn Jobs': {
        'senders': [
            'jobalerts-noreply@linkedin.com',
            'jobs-noreply@linkedin.com',
            'notifications-noreply@linkedin.com',
            'groups-noreply@linkedin.com',
            'newsletters-noreply@linkedin.com',
            'messaging-digest-noreply@linkedin.com',
        ],
    },
    '2026/Sports': {
        'senders': [
            'newsletter@mail.unrivaled.basketball',
            'servedmedia@substack.com',
            'no-reply@mailer.sportsengine.com',
            'no-reply@mailer-h.sportsengine.com',
            'donotreply@email.teamsnap.com',
            'no-reply@email.desertchampions.com',  # BNP Paribas Open
        ],
    },
    '2026/2026 Shopping': {
        'senders': [
            'no-reply@marsello.com',               # Annie's Blue Ribbon General Store
        ],
    },
    'Substack': {
        'senders': [
            '@substack.com',                       # All Substack newsletters
        ],
    },
    '2026/2026 Receipts': {
        'senders': [
            'noreply@uber.com',
            'no-reply@lyftmail.com',
            'no-reply@doordash.com',
            'noreply-us@klarna.com',
            'no-reply@amazon.com',
            'digital-noreply@amazon.com',
            'digital-no-reply@amazon.com',
            'no-reply@account.canva.com',
            'noreply@service.paypal.com',
            'noreply@jetblue.com',
            'noreply@billing.coned.com',
        ],
    },
}


def authenticate():
    creds = None
    # Force re-auth if token exists but may have old scopes
    if os.path.exists(TOKEN_FILE):
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


def get_list_unsubscribe(service, sender_email):
    results = service.users().messages().list(
        userId='me', q=f'from:{sender_email}', maxResults=1
    ).execute()
    messages = results.get('messages', [])
    if not messages:
        return None, None
    msg = service.users().messages().get(
        userId='me',
        id=messages[0]['id'],
        format='metadata',
        metadataHeaders=['List-Unsubscribe', 'List-Unsubscribe-Post']
    ).execute()
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    return headers.get('List-Unsubscribe'), headers.get('List-Unsubscribe-Post')


def send_unsubscribe_request(unsub_header, unsub_post_header=None):
    if not unsub_header:
        return False, "No List-Unsubscribe header"
    urls = re.findall(r'<(https?://[^>]+)>', unsub_header)
    mailtos = re.findall(r'<(mailto:[^>]+)>', unsub_header)

    # Try one-click POST first
    if urls and unsub_post_header and 'One-Click' in unsub_post_header:
        try:
            req = urllib.request.Request(
                urls[0], data=b'List-Unsubscribe=One-Click', method='POST'
            )
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=10) as r:
                return True, f"One-click POST → {urls[0]}"
        except Exception:
            pass

    # Try GET
    if urls:
        try:
            req = urllib.request.Request(urls[0])
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=10) as r:
                return True, f"GET → {urls[0]}"
        except Exception as e:
            return False, f"GET failed: {e}"

    if mailtos:
        return False, f"Mailto only (manual needed): {mailtos[0]}"

    return False, "Could not parse unsubscribe URL"


def archive_all_from_sender(service, sender_email):
    archived = 0
    page_token = None
    while True:
        kwargs = {'userId': 'me', 'q': f'from:{sender_email} in:inbox', 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token
        results = service.users().messages().list(**kwargs).execute()
        messages = results.get('messages', [])
        if not messages:
            break
        service.users().messages().batchModify(
            userId='me',
            body={'ids': [m['id'] for m in messages], 'removeLabelIds': ['INBOX']}
        ).execute()
        archived += len(messages)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return archived


def create_label(service, name):
    existing = service.users().labels().list(userId='me').execute()
    for label in existing.get('labels', []):
        if label['name'] == name:
            return label['id']
    label = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    return label['id']


def create_filters(service, senders, label_id):
    ok, failed = 0, []
    for sender in senders:
        try:
            service.users().settings().filters().create(
                userId='me',
                body={
                    'criteria': {'from': sender},
                    'action': {'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
                }
            ).execute()
            ok += 1
        except Exception as e:
            failed.append(f"{sender}: {e}")
        time.sleep(0.2)
    return ok, failed


def delete_all_from_sender(service, sender_email, mark_spam=False):
    deleted = 0
    page_token = None
    while True:
        kwargs = {'userId': 'me', 'q': f'from:{sender_email}', 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token
        results = service.users().messages().list(**kwargs).execute()
        messages = results.get('messages', [])
        if not messages:
            break
        ids = [m['id'] for m in messages]
        if mark_spam:
            service.users().messages().batchModify(
                userId='me',
                body={'ids': ids, 'addLabelIds': ['SPAM'], 'removeLabelIds': ['INBOX']}
            ).execute()
        else:
            service.users().messages().batchModify(
                userId='me',
                body={'ids': ids, 'addLabelIds': ['TRASH'], 'removeLabelIds': ['INBOX']}
            ).execute()
        deleted += len(messages)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return deleted


def apply_label_to_existing(service, senders, label_id):
    total = 0
    for sender in senders:
        page_token = None
        while True:
            kwargs = {'userId': 'me', 'q': f'from:{sender}', 'maxResults': 500}
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
                    'removeLabelIds': ['INBOX']
                }
            ).execute()
            total += len(messages)
            page_token = results.get('nextPageToken')
            if not page_token:
                break
    return total


def main():
    print("\n=== Gmail Action Script ===\n")

    print("Connecting to Gmail (you may need to approve access in your browser)...")
    service = authenticate()
    print("Connected!\n")

    # STEP 1: UNSUBSCRIBE
    print("=" * 60)
    print("STEP 1: UNSUBSCRIBING + ARCHIVING MARKETING EMAILS")
    print("=" * 60)

    results = []
    manual_needed = []

    for sender in UNSUBSCRIBE_SENDERS:
        print(f"\n  {sender}")
        unsub_header, unsub_post = get_list_unsubscribe(service, sender)
        if unsub_header:
            success, msg = send_unsubscribe_request(unsub_header, unsub_post)
            if success:
                print(f"    Unsubscribe: OK - {msg}")
            else:
                print(f"    Unsubscribe: Manual needed - {msg}")
                manual_needed.append(sender)
        else:
            success = False
            msg = "No unsubscribe header"
            print(f"    Unsubscribe: No header found (will just archive)")

        count = archive_all_from_sender(service, sender)
        print(f"    Archived: {count} emails")
        results.append({'sender': sender, 'unsubscribed': success, 'note': msg, 'archived': count})
        time.sleep(0.3)

    # STEP 2: DELETE + SPAM
    print("\n" + "=" * 60)
    print("STEP 2: DELETING + MARKING AS SPAM")
    print("=" * 60)

    for sender in DELETE_AND_SPAM_SENDERS:
        print(f"\n  {sender}")
        count = delete_all_from_sender(service, sender, mark_spam=True)
        print(f"    Marked as spam + deleted: {count} emails")
        time.sleep(0.3)

    for sender in DELETE_ONLY_SENDERS:
        print(f"\n  {sender}")
        count = delete_all_from_sender(service, sender, mark_spam=False)
        print(f"    Deleted: {count} emails")
        time.sleep(0.3)

    # STEP 3: CREATE LABELS
    print("\n" + "=" * 60)
    print("STEP 3: CREATING LABELS")
    print("=" * 60)

    label_ids = {}
    for name in LABEL_CONFIGS:
        lid = create_label(service, name)
        label_ids[name] = lid
        print(f"  ✓ {name}")

    # STEP 4: CREATE FILTERS
    print("\n" + "=" * 60)
    print("STEP 4: SETTING UP FILTERS FOR FUTURE EMAILS")
    print("=" * 60)

    for name, config in LABEL_CONFIGS.items():
        ok, failed = create_filters(service, config['senders'], label_ids[name])
        print(f"  {name}: {ok} filters created" + (f", {len(failed)} failed" if failed else ""))
        for f in failed:
            print(f"    ✗ {f}")

    # STEP 5: MOVE EXISTING EMAILS
    print("\n" + "=" * 60)
    print("STEP 5: ORGANIZING EXISTING EMAILS INTO LABELS")
    print("=" * 60)

    for name, config in LABEL_CONFIGS.items():
        count = apply_label_to_existing(service, config['senders'], label_ids[name])
        print(f"  {name}: {count} emails moved")

    # SUMMARY
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    successful = sum(1 for r in results if r['unsubscribed'])
    total_archived = sum(r['archived'] for r in results)
    print(f"\n  Unsubscribed: {successful}/{len(UNSUBSCRIBE_SENDERS)} senders")
    print(f"  Archived: {total_archived} emails removed from inbox")
    print(f"  Labels created: 2026/LinkedIn Jobs, 2026/Sports, 2026/2026 Shopping, 2026/2026 Receipts, Substack")

    if manual_needed:
        print(f"\n  ⚠ {len(manual_needed)} senders need manual unsubscribe:")
        for s in manual_needed:
            print(f"    - {s}")

    with open('action_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n  Full results saved to action_results.json")


if __name__ == '__main__':
    main()
