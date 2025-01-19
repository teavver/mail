import logging, subprocess, os
from .classes import AppConfig, CallbackHandlerConfig
from typing import Literal, Tuple, List
from imap_tools import MailBox, MailMessage, MailboxLoginError
from itertools import filterfalse


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

    def fetch_inbox(self, mode: Literal["recent", "all"]) -> Tuple[List[MailMessage]]:
        limit = (
            self.config.general.fetch_full
            if mode == "all"
            else self.config.general.fetch_recent
        )
        msgs_gen = (
            msg
            for msg in self.mailbox.fetch(limit=limit, reverse=True, charset="UTF-8")
        )
        eval_msgs = tuple([self.eval_mail(msg) for msg in msgs_gen])
        msgs = list(filterfalse(lambda x: x is None, eval_msgs))
        msgs, handlers = zip(*msgs) if msgs else (None, None)
        
        # TEMP
        for idx, handler in enumerate(handlers):
            if handler is not None:
                print(f"--> IDX: {idx} msg: {msgs[idx]}, ---- handler: {handler}")
                try:
                    assert(os.path.isfile(handler.exec_path), f"failed to invoke callback - path does not exist ({handler.exec_path})")
                    py_call = "python" if handler.python_ver == 2 else "python3"
                    res = subprocess.call([py_call, handler.exec_path])
                    logging.debug(f"callback res: {res}")
                except Exception as e:
                    logging.error(f"err during test invoke callback: {e}")
            
        #
        self.last_uid = msgs[-1].uid
        return msgs

    def eval_mail(self, mail: MailMessage) -> Tuple[MailMessage, CallbackHandlerConfig | None]:
        try:
            for handler in self.config.handlers:
                res = handler.get_pattern().match(mail.subject)
                if res:
                    logging.debug(f"eval: - subject: {mail.subject} - res: {res}")
                    return (mail, handler)
            return (mail, None)
        except Exception as e:
            logging.error(f"fail during eval_mail: {e}")
            return None
