#!/usr/bin/env python3
import os
import sqlite3
import urllib.request
import json
import io
import zipfile
import argparse
from datetime import datetime, timedelta

# ---------------------------------------------------------------------
MESSAGE_COUNTS_ENDPOINT = "/api/file-upload/whatsapp-counts"
MESSAGE_ARCHIVES_ENDPOINT = "/api/file-upload/whatsapp-chats"
# ---------------------------------------------------------------------


def main(api_key, test):
    # 1. Connect to SQLite
    db_path = os.path.expanduser(
        "~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
    )
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. Query to fetch all messages (without ORDER BY)
    query = """
    SELECT
        cs.ZCONTACTJID,      -- 0 partner_jid, e.g. "+1234567890@s.whatsapp.net"
        cs.ZPARTNERNAME,     -- 1 partner_name
        m.ZFROMJID,          -- 2 from_jid
        m.ZTOJID,            -- 3 to_jid
        m.ZTEXT,             -- 4 text
        m.ZMESSAGEDATE,      -- 5 message_date (Apple epoch)
        m.ZMESSAGETYPE,      -- 6 media_item
        mi.ZTITLE            -- 7 media_title (link title)
    FROM ZWACHATSESSION cs
    JOIN ZWAMESSAGE m
         ON (m.ZFROMJID = cs.ZCONTACTJID OR m.ZTOJID = cs.ZCONTACTJID)
    LEFT JOIN ZWAMEDIAITEM mi
          ON m.Z_PK = mi.ZMESSAGE
    WHERE cs.ZCONTACTJID NOT LIKE '%@g.us'
    """
    cursor.execute(query)

    # Remove partner_data and partner_messages dictionaries
    # Replace with a single messages list
    messages = []
    partner_data = {}

    apple_epoch = datetime(2001, 1, 1)

    for row in cursor:
        partner_jid = row[0] or ""
        partner_name = row[1] or "?"
        from_jid = row[2] or ""
        text = row[4] or ""
        msg_date_apple_epoch = row[5] or 0
        message_type = row[6]
        media_title = row[7]

        # Parse out phone number from partner_jid by splitting at '@'
        # (If there's no '@', we'll just keep the original partner_jid.)
        phone_number = (
            "+" + partner_jid.split("@")[0] if "@" in partner_jid else partner_jid
        )

        # Initialize partner data if needed
        if partner_name not in partner_data:
            partner_data[partner_name] = {
                "phone_number": phone_number,
                "message_count": 0,
            }

        partner_data[partner_name]["message_count"] += 1

        # Determine from/to
        if from_jid == partner_jid:
            from_name = partner_name
            to_name = "me"
        else:
            from_name = "me"
            to_name = partner_name

        # Convert timestamp
        dt = apple_epoch + timedelta(seconds=msg_date_apple_epoch)
        dt_str = dt.isoformat()

        # Add message to single messages list
        messages.append(
            {
                "datetime": dt_str,
                "content": text,
                "from": from_name,
                "to": to_name,
                "message_type": message_type,
                "media_title": media_title,
            }
        )

    cursor.close()
    conn.close()

    print("Creating in-memory ZIP with chat archives...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        json_str = json.dumps(messages, ensure_ascii=False, indent=2)
        zf.writestr("messages.json", json_str)

    BASE_URL = "http://localhost:3000" if test else "https://enclaveid.com"

    zip_data = zip_buffer.getvalue()
    print("Uploading message archives...")
    post_zip(BASE_URL + MESSAGE_ARCHIVES_ENDPOINT, zip_data, api_key)

    print("Uploading message counts...")
    post_json(BASE_URL + MESSAGE_COUNTS_ENDPOINT, partner_data, api_key)


def post_json(url, data_dict, api_key):
    """Send a JSON POST using urllib."""
    payload_bytes = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req) as f:
        return f.read().decode("utf-8")


def post_zip(url, zip_bytes, api_key):
    """Send raw binary ZIP data as POST using urllib."""
    req = urllib.request.Request(
        url,
        data=zip_bytes,
        method="POST",
        headers={
            "Content-Type": "application/zip",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req) as f:
        return f.read().decode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read WhatsApp ChatStorage.sqlite and send data via POST."
    )
    parser.add_argument("--api-key", required=True, help="API Key for your endpoints.")
    parser.add_argument("--test", action="store_true", help="Test mode.")
    args = parser.parse_args()
    main(args.api_key, args.test)
