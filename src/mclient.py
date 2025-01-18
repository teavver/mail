import threading, logging
from typing import Literal
from .classes import MailHostConfig
from imap_tools import MailBox, MailboxLoginError


class MailClient:
    def __init__(self, host_config: MailHostConfig):
        self.mailbox = None
        self.host_config = host_config
        self.last_email_id = None
        self.all_email_ids = []
        self.lock = threading.Lock()

    def login(self, login, pwd) -> MailBox:
        try:
            mail = MailBox(self.host_config.host, self.host_config.port, 60).login(
                login, pwd
            )
            self.mailbox = mail
            return mail
        except MailboxLoginError as e:
            logging.error(f"mailbox login err: {e}")
        except Exception as e:
            logging.error(f"mailbox login unknown err: {e}")

    def fetch_inbox(self, mode: Literal["recent", "all"]):
        limit = 500 if mode == "all" else 50  # TODO: FIOX
        msgs_gen = (
            msg for msg in self.mail.fetch(limit=limit, reverse=True, charset="UTF-8")
        )
        return list(msgs_gen)

    def check_for_existing_emails(self):
        pass
