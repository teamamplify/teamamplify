"""
Email helper for the /aria skill.

Called by the skill after writing the report to disk.
Usage: python aria/email_report.py <html_path> <text_path> <subject>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from aria import emailer, config

if len(sys.argv) < 4:
    print("Usage: python aria/email_report.py <html_path> <text_path> <subject>")
    sys.exit(1)

html_path, text_path, subject = sys.argv[1], sys.argv[2], sys.argv[3]

with open(html_path, "r", encoding="utf-8") as fh:
    html_body = fh.read()

with open(text_path, "r", encoding="utf-8") as fh:
    text_body = fh.read()

delivered = emailer.send(
    subject=subject,
    html_body=html_body,
    text_body=text_body,
    from_email=config.FROM_EMAIL,
    to_email=config.TO_EMAIL,
)

if delivered:
    print(f"Email delivered to {config.TO_EMAIL}")
    sys.exit(0)
else:
    print("Email delivery failed — check logs")
    sys.exit(1)
