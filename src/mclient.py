import logging, re
from typing import Literal
from imap_tools import MailBox, MailMessage, MailboxLoginError
from .classes import AppConfig


class MailClient:
    def __init__(self, config: AppConfig):
        self.config = config
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
        patterns = [h.pattern for h in self.config.handlers]
        # subjects = [msg.subject for msg in msgs_gen]
        # for m in subjects:
        #     print(m)
        msgs = [self.eval_mail(msg, patterns) for msg in msgs_gen]
        self.last_uid = msgs[-1].uid
        return msgs
        # return []

    def eval_mail(self, mail: MailMessage, patterns: str):
        try:
            for p in patterns:
                # TODO: test regex pre this part
                expr = re.compile(p)
                res = expr.match(mail.subject)
                if res is not None: logging.debug(f"eval: - subject: {mail.subject} - res: {res}")
            return mail
        except Exception as e:
            logging.error(f"fail during eval_mail: {e}")
