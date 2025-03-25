import imaplib
import email
from email.policy import default


def fetch_emails(imap_host, username, password, mailbox="INBOX"):
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(username, password)
    mail.select(mailbox)
    _, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email, policy=default)
        emails.append(msg)
    mail.logout()
    return emails


def parse_email_content(msg):
    body = ""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body += part.get_payload(decode=True).decode(errors='ignore')
            elif "attachment" in part.get("Content-Disposition", ""):
                filename = part.get_filename()
                content = part.get_payload(decode=True)
                attachments.append((filename, content))
    else:
        body += msg.get_payload(decode=True).decode(errors='ignore')
    return body, attachments