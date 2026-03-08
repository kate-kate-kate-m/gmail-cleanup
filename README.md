# Gmail Cleanup & Automation

## How to run scripts manually
All scripts must be run from inside the `gmail-cleanup` folder using the virtual environment:
```
cd ~/gmail-cleanup && venv/bin/python3 <script_name>.py
```

---

## Scripts

### gmail_cleanup.py
Read-only scanner. Scans your inbox for subscription/newsletter emails and groups them by sender. Does NOT make any changes. Outputs results to `scan_results.json`.

### gmail_auto_sort.py
Runs automatically every 10 minutes via launchd. Moves emails matching certain rules out of your inbox into holding labels:
- Emails from `*@substack.com` → moved to **Substack** label (held until 4pm delivery)
- Emails from retailer domains → moved to **2026 Shopping** label

Logs activity to `autosort.log`.

### gmail_substack_deliver.py
Runs automatically every 15 minutes via GitHub Actions, but only delivers emails that haven't been delivered yet. At/after 4pm ET, finds all emails in the **Substack** label from the last 24 hours that don't have the `substack-delivered` Gmail label, moves them to your inbox, and stamps them with `substack-delivered` so they're never re-delivered — even after you read and file them away.

### gmail_archive.py
One-time script. Creates a "2025 archive" label and moves all inbox emails older than December 4, 2025 into it.

### gmail_mark_read.py
One-time script. Marks all inbox emails as read and moves them to a "2026 cleanup" label. Used for inbox zero resets.

### gmail_nest_labels.py
One-time script. Used for label organization.

### gmail_action.py
Utility script for taking actions on emails (details TBD).

---

## Automated jobs (launchd)

Both agents are stored in `~/Library/LaunchAgents/` and load automatically on login.

| Agent | Script | Schedule |
|---|---|---|
| com.kate.gmail.autosort | gmail_auto_sort.py | Every 10 minutes |
| com.kate.gmail.substackdeliver | gmail_substack_deliver.py | Every 15 min (delivers once/day at or after 4pm ET) |

### To reload an agent after changes:
```
launchctl unload ~/Library/LaunchAgents/<agent-name>.plist
launchctl load ~/Library/LaunchAgents/<agent-name>.plist
```

---

## Weekly maintenance
Run the manual scan weekly to catch any remaining spam/subscription emails that the auto-sort doesn't handle:
1. `venv/bin/python3 gmail_cleanup.py` — scans and outputs to `scan_results.json`
2. Review results, then run `venv/bin/python3 gmail_action.py` to take action

Do this for about a month until the inbox is consistently clean.

## Session log

### 2026-03-07
- Added GitHub Actions workflows to run autosort and substackdeliver in the cloud

### 2026-03-08
- Fixed bug in `gmail_substack_deliver.py` where Substack emails were re-delivered to inbox every 15 minutes after 4pm. Root cause: the script used a local flag file (`last_delivered.txt`) to track delivery, but GitHub Actions uses a fresh runner each run so the file never persisted. Fix: replaced flag file with a hidden Gmail label (`substack-delivered`) that gets stamped on each email at delivery time. The search query now excludes already-delivered emails.
