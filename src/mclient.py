import logging
from .classes import AppConfig, CallbackHandlerConfig
from typing import Literal, Tuple, List
from imap_tools import MailBox, MailMessage, MailboxLoginError
from re import Pattern


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

    def fetch_inbox(self, mode: Literal["recent", "all"]) -> Tuple[List[MailMessage], ]:
        limit = (
            self.config.general.fetch_full
            if mode == "all"
            else self.config.general.fetch_recent
        )
        msgs_gen = (
            msg
            for msg in self.mailbox.fetch(limit=limit, reverse=True, charset="UTF-8")
        )
        x = self.config.handlers[0]
        print(f"test: {x}")
        # msgs, handlers = [self.eval_mail(msg) for msg in msgs_gen]
        # self.last_uid = msgs[-1].uid
        # print(f"msgs: {msgs}")
        # print(f"handlers: {handlers}")
        # return (msgs, handlers)

    # def eval_mail(self, mail: MailMessage) -> Tuple[MailMessage, CallbackHandlerConfig | None]:
    #     try:
    #         for handler in self.config.handlers:
    #             res = handler.pattern.match(mail.subject)
    #             if res:
    #                 # logging.debug(f"eval: - subject: {mail.subject} - res: {res}")
    #                 return (mail, handler)
    #         return (mail, None)
    #     except Exception as e:
    #         logging.error(f"fail during eval_mail: {e}")
    #         return None
