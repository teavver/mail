import imaplib, email, threading, logging, re, sys
from email.header import decode_header
from interval.interval import ThreadJob
from classes.classes import MailConfig, MailServer
import util.util as util

# TEMP CONFIG
MAX_HISTORY = 500


def connect_to_gmail(config: MailConfig):
    mail = imaplib.IMAP4_SSL(config.server.host, int(config.server.port))
    mail.login(config.email, config.pwd)
    return mail


class MailChecker:
    def __init__(self, mail):
        self.mail = mail
        self.last_email_id = None
        self.all_email_ids = []
        self.lock = threading.Lock()
        
    def search_inbox(self):
        self.mail.select("inbox", True)
        # ok, mail_ids = self.mail.search(None, "ALL")
        # ok, messages = self.mail.search(None, "RECENT")
        # ok, messages = self.mail.uid("search", None, "ALL")
        # ok, messages = self.mail.sort("REVERSE DATE", 'UTF-8', "ALL")
        if ok != "OK":
            logging.error(f"Failed to search mail inbox")
            sys.exit(1)
        # return mail_ids[0].split()[-MAX_HISTORY:]
        print(len(messages[0]))
        return messages[0].split()[-MAX_HISTORY:]

    # Detect & match incoming
    def check_for_new_emails(self):
        with self.lock:
            last_email_id = self.last_email_id

        logging.info("- checking for new mail....")
        logging.info(f"- current last_email_id: {last_email_id}")

        self.mail.select("inbox")
        _, messages = self.mail.search(None, "ALL")
        email_ids = messages[0].split()

        if not email_ids:
            logging.info("no mail")
            return last_email_id

        latest_email_id = email_ids[-1]
        logging.info(f"- last_id: {last_email_id}, latest_id: {latest_email_id}")

        if latest_email_id != last_email_id:
            _, msg_data = self.mail.fetch(latest_email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            logging.info(f"- new email subject: '{subject}'")
            with self.lock:
                self.last_email_id = latest_email_id
        logging.info("-")
        return last_email_id
    
    def check_for_existing_emails(self): pass


def main():
    args = util.get_args()
    env = util.get_env()

    server = MailServer(env["MAIL_SERVER"], env["MAIL_PORT"])
    config = MailConfig(env["MAIL_ADDR"], env["MAIL_PWD"], server)
    mail = connect_to_gmail(config)
    mail_checker = MailChecker(mail)
    event = threading.Event()
    x = mail_checker.search_inbox()
    print(len(x))

    # try:
    #     k = ThreadJob(lambda: mail_checker.check_for_new_emails(), event, 5)
    #     k.start()
    #     logging.info("- run app ok")

    # except KeyboardInterrupt:
    #     logging.info("signing out...")
    #     mail.logout()


if __name__ == "__main__":
    main()
