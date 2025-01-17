import imaplib, email, threading, logging, re, sys
from email.header import decode_header
from interval.interval import ThreadJob
from classes.classes import MailConfig, MailHostConfig
from imap_tools import MailBox, MailboxLoginError
from typing import Literal
import util.util as util

# import mclient.mclient as MailClient
from mclient.mclient import MailClient


def mail_login(config: MailConfig) -> MailBox:
    try:
        mail = MailBox(config.host.server, config.host.port, 60).login(
            config.email, config.pwd
        )
        return mail
    except MailboxLoginError as e:
        logging.error(f"mailbox login err: {e}")
    except Exception as e:
        logging.error(f"mailbox login unknown err: {e}")


def main():
    args = util.get_args()
    env = util.get_env()

    valid_pattern = util.test_regex(args.regex)
    if valid_pattern == False:
        sys.exit(1)

    host = MailHostConfig(env["MAIL_HOST"], env["MAIL_PORT"])
    config = MailConfig(env["MAIL_ADDR"], env["MAIL_PWD"], host)
    mail = mail_login(config)
    logging.debug(mail.login_result)
    mail_checker = MailClient(mail, valid_pattern)
    # event = threading.Event()
    msgs = mail_checker.fetch_inbox("recent")
    matching = [msg.subject for msg in msgs if valid_pattern.match(msg.subject) is not None]
    print(matching)
    # for msg in msgs:
    #     match = valid_pattern.match(msg.subject)
    #     print(f"match: {match}")
    # logging.debug(f"matching mails: {matching}")

    # try:
    #     k = ThreadJob(lambda: mail_checker.check_for_new_emails(), event, 5)
    #     k.start()
    #     logging.info("- run app ok")


if __name__ == "__main__":
    main()
