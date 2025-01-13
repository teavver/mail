import imaplib, email, os, sys
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

# Your Gmail credentials
EMAIL = os.getenv('EMAIL')
APP_PASSWORD = os.getenv('APP_PASSWORD')

def connect_to_gmail():
    # Connect to the Gmail IMAP server
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    
    # Log in to your account
    mail.login(EMAIL, APP_PASSWORD)
    
    return mail

def read_emails(mail):
    # Select the mailbox you want to read from (e.g., INBOX)
    mail.select("inbox")
    
    # Search for all emails in the selected mailbox
    status, messages = mail.search(None, 'ALL')
    
    # Convert messages to a list of email IDs
    email_ids = messages[0].split()
    
    # Read the latest email (you can change the index to read other emails)
    latest_email_id = email_ids[-1]
    
    # Fetch the email by ID
    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
    
    # Parse the email content
    msg = email.message_from_bytes(msg_data[0][1])
    
    # Decode email subject
    subject, encoding = decode_header(msg['Subject'])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else 'utf-8')
    
    print(f'Subject: {subject}')
    
def main():
    if EMAIL is None or APP_PASSWORD is None:
        print('Missing env keys')
        sys.exit(1)
    
    mail = connect_to_gmail()
    read_emails(mail)
    mail.logout()

if __name__ == "__main__":
    main()
