import logging
from typing import Literal
from imap_tools import MailBox, MailboxLoginError
from .classes import MailHostConfig, GeneralAppSettings


class MailClient:
    def __init__(self, gen_settings: GeneralAppSettings, host_config: MailHostConfig):
        self.settings = gen_settings
        self.mailbox = None
        self.host_config = host_config
        self.uids = []

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
        limit = self.settings.fetch_full if mode == "all" else self.settings.fetch_recent
        msgs_gen = (
            msg for msg in self.mailbox.fetch(limit=limit, reverse=True, charset="UTF-8")
        )
        msgs = list(msgs_gen)
        self.uids = [msg.uid for msg in msgs]
        return msgs
