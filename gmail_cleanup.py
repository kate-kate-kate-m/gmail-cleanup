import os
import json
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.settings.basic']
CREDS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Senders already handled — skip these in the scan
ALREADY_HANDLED = {
    'info@n.skinstore.com', 'hello@thesill.com', 'sperry@mailing.sperry.com',
    'teamzoom@e.zoom.us', 'webinars@e.zoom.us',
    'newsletter@hhm.healthyhabitatmarket.com',
    'newsletter@blog.innovationsandhealth.com',
    'dig@emails.thanx.com', 'joecoffee@emails.thanx.com',
    'noreply@hello.klarna.com', 'no-reply@messages.doordash.com',
    'no-reply@marketing.lyftmail.com', 'no-reply@f45training.com',
    'no-reply@m.ouraring.com', 'email@hello.babbel.com',
    'no-reply@gowatch.nbc.com', 'advertise-noreply@global.metamail.com',
    'no-reply@channels.primevideo.com', 'no-reply@notifications.whoop.com',
    'donotreply@e.zeelool.com', 'marketing@newsletter.eatokra.com',
    'info@dailyprovisionsnyc.com', 'emails@thanx.com',
    'hello@onepercentimprovements.convertkit.com',
    'no-reply@mail.goodreads.com', 'editors-noreply@linkedin.com',
    'messages-noreply@linkedin.com',
    # Kept senders
    'jobalerts-noreply@linkedin.com', 'jobs-noreply@linkedin.com',
    'notifications-noreply@linkedin.com', 'groups-noreply@linkedin.com',
    'newsletters-noreply@linkedin.com', 'messaging-digest-noreply@linkedin.com',
    'newsletter@mail.unrivaled.basketball', 'servedmedia@substack.com',
    'noreply@uber.com', 'no-reply@lyftmail.com', 'no-reply@doordash.com',
    'noreply-us@klarna.com', 'no-reply@amazon.com', 'digital-noreply@amazon.com',
    'digital-no-reply@amazon.com', 'no-reply@account.canva.com',
    'noreply@service.paypal.com', 'noreply@jetblue.com',
    'noreply@billing.coned.com',
    # Batch 2
    'noreply@email.streeteasy.com', 'noreply@streeteasy.com',
    'noreply@goodamerican.com',
    'noreply@a.email.hbr.org', 'noreply@email.hbr.org',
    'noreply@m.klarna.com', 'noreply@e.klarna.com',
    'noreply@redditmail.com',
    'no-reply@is.email.nextdoor.com', 'no-reply@rs.email.nextdoor.com',
    'noreply@ms.email.nextdoor.com',
    'donotreply@e.society6.com', 'donotreply@t.society6.com',
    'newsletter@theskint.com', 'noreply@r.groupon.com',
    'newsletter@shopfavoritedaughter.com', 'no-reply@email.peacocktv.com',
    'donotreply@afterpay.com', 'newsletter@cravingsbychrissyteigen.com',
    'newsletter@citywinery.com', 'newsletter@blavity.com',
    'newsletter@mail.blavity.com', 'noreply@skims.com',
    'noreply@e.lifetime.life', 'noreply@t.lifetime.life', 'noreply@emails.lifetime.life',
    'advertise-noreply@support.facebook.com', 'noreply@business-updates.facebook.com',
    'no-reply@yelp.com', 'no-reply@mail.yelp.com',
    'noreply@mail.amcentertainment.com', 'noreply@email.amctheatres.com',
    'donotreply@shondaland.com', 'noreply@hyrox.com',
    'no-reply@marketing.espnmail.com', 'espnpromotions@espnmail.com',
    'newsletter@illesteva.com', 'newsletter@service.tiktok.com',
    'no-reply@primevideo.com', 'donotreply@23andme.com', 'noreply@mail.23andme.com',
    'newsletter@reply.ticketmaster.com', 'noreply@send.candid.org', 'noreply@candid.org',
    'no-reply@mailer.sportsengine.com', 'no-reply@mailer-h.sportsengine.com',
    'donotreply@email.teamsnap.com',
    # Batch 3
    'no-reply@mail.joinfound.com', 'newsletter@nysun.com',
    'newsletter@email.pvolve.com', 'noreply@employer-network.com',
    'updates@truemed.com', 'noreply@shop.app', 'newsletter@bergesinstitute.com',
    'no-reply@notifications.arketa.co', 'arketa-noreply@arketa.co',
    'pollers@thepandaresearchedition.com', 'member@yourpandadept.com',
    'news@pandaresearch-survs.com', 'no-reply@marketing.gogreenwood.com',
    'newsletter@thehomeedit.com', 'newsletter@canadapooch.com',
    'noreply@canadapooch.com', 'noreply@shopthenovogratz.com', 'noreply@thenovogratz.com',
    'donotreply@loseit.com', 'no-reply@compass.com', 'noreply@e.lululemon.com',
    'newsletter@oppositewall.com', 'noreply@emails.castlery.com',
    'no-reply@politicsny.com', 'no-reply@stumblemail.com', 'noreply@moviepass.com',
    'no-reply@email.nbc.com', 'newsletter@cruz.senate.gov', 'noreply@regenics.com',
    'staff@dlcc.org', 'noreply@email.bestegg.com',
    'no-reply@marketing.zerolongevity.com', 'no-reply@marketing.zerofasting.com',
    'newsletter@dosomething.org', 'newsletter@metrowize.com', 'newsletter@bdwayinfo.com',
    'noreply@summersalt.com', 'newsletter@mail.monicavinader.com',
    'noreply@smc.waxcenter.com', 'no-reply@newsletter.tp-link.com',
    'tplinkus@newsletter.tp-link.com', 'donotreply@ismellgreat.com',
    'no-reply@passionplanner.com', 'noreply@medium.com', 'no-reply@postmates.com',
    'newsletter@official.nikestrength.com', 'wordsofwomennewsletter@ghost.io',
    'no-reply@joindeleteme.com', 'deleteme+newsletter@joindeleteme.com',
    'noreply@fentybeauty.com', 'no-reply@mail.kissusa.com', 'noreply@e.dyson.com',
    'noreply@email.usopen.org', 'warnerbros@updates.warnerbros.com',
    'noreply@unikwax.com', 'no-reply@flywheelsports.com', 'hello@news.bodyboss.com',
    'noreply@tnuck.com', 'noreply@kaiyo.com',
    'email.replies@newsletter.mobilize.us', 'noreply@mobilize.us',
    'communications@maps.org', 'newYorker@newsletter.newyorker.com',
    'newsletter@adamgrant.net', 'newsletter@hechingerreport.org',
    'noreply@gm.chief.com', 'no-reply@m.sofi.org', 'no-reply@o.sofi.org',
    'no-reply@r.sofi.com', 'noreply@results.equinox.com',
    'newsletter@womenshealthmag.com', 'no-reply@theskimm.com',
    'hrweek@e.shrm.org', 'hrmagazine@e.shrm.org', 'noreply@robinhood.com',
    'noreply@wayfair.com', 'noreply@paintnite.com', 'donotreply@showclix.com',
    'noreply@f.anthropologie.com', 'noreply@zenoti.com',
    'no-reply@email.signalaward.com', 'newsletter@email-nmss.org',
    'no-reply@emailoutreach.wharton.upenn.edu', 'noreply@swingleft.org',
    'no-reply@amazonmusic.com', 'no-reply@msg.amazonmusic.com',
    'no-reply@announce.fiverr.com', 'donotreply@bestyetmarket.com',
    'no-reply@corkcicle.com', 'info@naca.org', 'no-reply@tryfi.com',
    'noreply@prezi.com', 'noreply@upwork.com', 'donotreply@upwork.com',
    # Batch 4
    'no-reply@substack.com', 'donotreply@match.indeed.com',
    'no-reply@email.desertchampions.com', 'no-reply@loox.io',
    'no-reply@email.claude.com', 'noreply@canarytechnologies.com',
    'noreply@reminder.eventbrite.com', 'no-reply+16044926@toast-restaurants.com',
    'cscm-newsletter@mail.beehiiv.com', 'security-noreply@linkedin.com',
    'noreply@mail.app.supabase.io', 'no-reply@marsello.com',
    'noreply@notify.thinkific.com', 'no-reply+430af0c1@toast-restaurants.com',
    'noreply@projectrepat.com', 'noreply@h5.hilton.com',
    'noreply@e.stmarysclothingdrive.com', 'no-reply@info.gusto.com',
    'noreply@engage.covetruspharmacy.com', 'noreply@axs.com',
    'donotreply-membercomm@email.anthem.com', 'no-reply+8f04252d@toast-restaurants.com',
    'no-reply@ashbyhq.com', 'no-reply@booksy.com',
    'noreply.invitations@trustpilotmail.com', 'noreply@email.legalzoom.com',
    # Batch 5
    'hello@timeleft.com', 'hello@send.checkmatetoday.com',
    'info@update.rackroomshoes.com', 'hello@votefwd.org',
    'news@email.webbyawards.com', 'hello@831stories.com',
    'no-reply@cuddlduds.com', 'info@marketing.mlbemail.com',
    'hello@news.na.hyrox.com', 'info@email-nmss.org',
    'info@jewishaction.us', 'marketing@evebyboz.com',
    'hello@hello-sunshine.com', 'info@filmpittsburgh.org',
    'hello@knkg.com', 'americanexpress@member.americanexpress.com',
    'info@eml.upstart.com', 'info@hudsonsailing.org',
    'info@arborteas.com', 'info@email.signalaward.com',
    'info@sheshouldrun.org', 'formfitnessbk@info-formfitnessbk.com',
    'hello@libro.fm', 'info@morancompany.com',
    'hello@marisafalcon.com', 'simong@goldenpenwriting.info',
    'info@jfrej.org', 'no-reply@youtube.com',
}


def authenticate():
    creds = None
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
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def get_all_subscription_emails(service):
    """Paginate through ALL matching emails, not just the first 500."""
    seen_ids = set()
    queries = [
        'list-unsubscribe newer_than:7d',
        'from:noreply OR from:no-reply OR from:newsletter OR from:updates OR from:donotreply newer_than:7d',
        'from:info OR from:hello OR from:marketing OR from:news OR from:deals OR from:offers OR from:promotions newer_than:7d',
    ]
    for query in queries:
        page_token = None
        page = 0
        while True:
            page += 1
            kwargs = {'userId': 'me', 'q': query, 'maxResults': 500}
            if page_token:
                kwargs['pageToken'] = page_token
            response = service.users().messages().list(**kwargs).execute()
            for msg in response.get('messages', []):
                seen_ids.add(msg['id'])
            page_token = response.get('nextPageToken')
            print(f"  Query '{query[:40]}...' — page {page}, {len(seen_ids)} total so far")
            if not page_token:
                break
            time.sleep(0.2)
    return list(seen_ids)


def get_email_details(service, msg_id):
    msg = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='metadata',
        metadataHeaders=['From', 'Subject', 'List-Unsubscribe', 'Date']
    ).execute()
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    return {
        'id': msg_id,
        'from': headers.get('From', 'Unknown'),
        'subject': headers.get('Subject', '(no subject)'),
        'date': headers.get('Date', ''),
        'has_unsubscribe': 'List-Unsubscribe' in headers,
        'unsubscribe_header': headers.get('List-Unsubscribe', ''),
    }


def extract_email_address(from_field):
    """Pull just the email address from a From: field."""
    import re
    match = re.search(r'<([^>]+)>', from_field)
    if match:
        return match.group(1).lower()
    return from_field.lower().strip()


def group_by_sender(emails):
    senders = {}
    for email in emails:
        sender = email['from']
        if sender not in senders:
            senders[sender] = []
        senders[sender].append(email)
    return senders


def main():
    print("\n=== Gmail Deep Scan ===")
    print("READ-ONLY — No changes will be made\n")

    print("Connecting to Gmail...")
    service = authenticate()
    print("Connected!\n")

    print("Scanning ALL subscription emails (this will take several minutes)...")
    msg_ids = get_all_subscription_emails(service)
    print(f"\nFound {len(msg_ids)} total emails. Loading details...\n")

    emails = []
    for i, msg_id in enumerate(msg_ids):
        if i % 100 == 0 and i > 0:
            print(f"  Processing {i}/{len(msg_ids)}...")
        try:
            details = get_email_details(service, msg_id)
            emails.append(details)
        except Exception:
            pass
        if i % 50 == 0:
            time.sleep(0.1)  # gentle rate limiting

    senders = group_by_sender(emails)
    sender_list = sorted(senders.items(), key=lambda x: len(x[1]), reverse=True)

    # Filter out already-handled senders
    new_senders = [
        (sender, msgs) for sender, msgs in sender_list
        if extract_email_address(sender) not in ALREADY_HANDLED
    ]

    print(f"\n=== {len(new_senders)} NEW SENDERS (not yet handled) ===\n")
    print(f"{'#':<5} {'EMAILS':<8} {'CAN UNSUB?':<12} SENDER")
    print("-" * 80)
    for i, (sender, msgs) in enumerate(new_senders, 1):
        has_unsub = any(m['has_unsubscribe'] for m in msgs)
        unsub_marker = "YES" if has_unsub else "no"
        print(f"{i:<5} {len(msgs):<8} {unsub_marker:<12} {sender[:60]}")

    # Save results
    output = {
        'total_emails_scanned': len(emails),
        'total_senders_found': len(senders),
        'new_senders_count': len(new_senders),
        'new_senders': {
            sender: {
                'count': len(msgs),
                'has_unsubscribe': any(m['has_unsubscribe'] for m in msgs),
                'sample_subjects': [m['subject'] for m in msgs[:3]],
                'message_ids': [m['id'] for m in msgs]
            }
            for sender, msgs in new_senders
        }
    }

    with open('scan_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to scan_results.json")
    print("NO CHANGES HAVE BEEN MADE.")
    print("Share these results with Claude to decide next steps.")


if __name__ == '__main__':
    main()
