import imaplib, email, threading, logging, re, sys
from email.header import decode_header
from interval.interval import ThreadJob
from classes.classes import MailConfig, MailHostConfig
from imap_tools import MailBox, MailboxLoginError
from typing import Literal
import util.util as util

# TEMP CONFIG
FETCH_RECENT = 5
FETCH_MAX = 500


type MailFetchMode = Literal["recent", "all"]


def mail_login(config: MailConfig) -> MailBox:
    try:
        mail = MailBox(config.host.server, config.host.port, 60).login(config.email, config.pwd)
        return mail
    except MailboxLoginError as e:
        logging.error(f"mailbox login err: {e}")
    except Exception as e:
        logging.error(f"mailbox login unknown err: {e}")


class MailChecker:
    def __init__(self, mail: MailBox):
        self.mail = mail
        self.last_email_id = None
        self.all_email_ids = []
        self.lock = threading.Lock()

    def fetch_inbox(self, mode: MailFetchMode):
        limit = FETCH_MAX if mode == "all" else FETCH_RECENT
        msgs_gen = (msg for msg in self.mail.fetch(limit=limit, reverse=True))
        msgs = list(msgs_gen)
        return msgs

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

    def check_for_existing_emails(self):
        pass


def main():
    args = util.get_args()
    env = util.get_env()

    host = MailHostConfig(env["MAIL_HOST"], env["MAIL_PORT"])
    config = MailConfig(env["MAIL_ADDR"], env["MAIL_PWD"], host)
    mail = mail_login(config)
    logging.debug(mail.login_result)
    mail_checker = MailChecker(mail)
    event = threading.Event()
    mail_checker.fetch_inbox("recent")

    # try:
    #     k = ThreadJob(lambda: mail_checker.check_for_new_emails(), event, 5)
    #     k.start()
    #     logging.info("- run app ok")

    # except KeyboardInterrupt:
    #     logging.info("signing out...")
    #     mail.logout()


if __name__ == "__main__":
    main()
