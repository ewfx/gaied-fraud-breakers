def extract_text_from_email(msg):
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
