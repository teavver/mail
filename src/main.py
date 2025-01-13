import imaplib, email, os, sys, threading
from email.header import decode_header
from dotenv import load_dotenv
from interval.interval import ThreadJob

load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")


def connect_to_gmail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, APP_PASSWORD)
    return mail


class MailChecker:
    def __init__(self, mail):
        self.mail = mail
        self.last_email_id = None
        self.lock = threading.Lock()

    def check_for_new_emails(self):
        with self.lock:
            last_email_id = self.last_email_id

        print("- checking for new mail....")
        print(f"- current last_email_id: {last_email_id}")

        self.mail.select("inbox")
        _, messages = self.mail.search(None, "ALL")
        email_ids = messages[0].split()

        if not email_ids:
            print("no mail")
            return last_email_id

        latest_email_id = email_ids[-1]
        print(f"- last_id: {last_email_id}, latest_id: {latest_email_id}")

        if latest_email_id != last_email_id:
            _, msg_data = self.mail.fetch(latest_email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            print(f"- new email subject: '{subject}'")
            with self.lock:
                self.last_email_id = latest_email_id

        print("-")
        return last_email_id


def main():
    if EMAIL is None or APP_PASSWORD is None:
        print("missing env keys")
        sys.exit(1)

    mail = connect_to_gmail()
    mail_checker = MailChecker(mail)
    event = threading.Event()

    try:
        k = ThreadJob(lambda: mail_checker.check_for_new_emails(), event, 5)
        k.start()
        print("- run app ok")

    except KeyboardInterrupt:
        print("signing out...")
        mail.logout()


if __name__ == "__main__":
    main()
