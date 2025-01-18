import logging, re
from .classes import AppConfig
from typing import Literal
from imap_tools import MailBox, MailMessage, MailboxLoginError
from re import Pattern


class MailClient:
    def __init__(self, config: AppConfig, patterns: list[Pattern]):
        self.config = config
        self.patterns = patterns
        self.mailbox = None
        self.last_uid = None

    def login(self, login, pwd) -> MailBox:
        try:
            mail = MailBox(self.config.mail.host, self.config.mail.port, 60).login(
                login, pwd
            )
            self.mailbox = mail
            return mail
        except MailboxLoginError as e:
            logging.error(f"mailbox login err: {e}")
        except Exception as e:
            logging.error(f"mailbox login unknown err: {e}")

    def fetch_inbox(self, mode: Literal["recent", "all"]):
        limit = (
            self.config.general.fetch_full
            if mode == "all"
            else self.config.general.fetch_recent
        )
        msgs_gen = (
            msg
            for msg in self.mailbox.fetch(limit=limit, reverse=True, charset="UTF-8")
        )
        msgs = [self.eval_mail(msg) for msg in msgs_gen]
        self.last_uid = msgs[-1].uid
        return msgs

    def eval_mail(self, mail: MailMessage):
        try:
            for p in self.patterns:
                res = p.match(mail.subject)
                if res is not None: logging.debug(f"eval: - subject: {mail.subject} - res: {res}")
            return mail
        except Exception as e:
            logging.error(f"fail during eval_mail: {e}")
