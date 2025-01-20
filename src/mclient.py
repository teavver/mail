import logging, subprocess, os
from .classes import AppConfig, ScriptConfig
from typing import Literal, Tuple
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
            logging.info(f"mailbox login success")
            return mail
        except MailboxLoginError as e:
            logging.error(f"mailbox login err: {e}")
            return None
        except Exception as e:
            logging.error(f"mailbox login unknown err: {e}")
            return None

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
        eval_msgs = tuple([self.eval_pattern(msg) for msg in msgs_gen])
        res = list(filterfalse(lambda x: x is None or x[1] is None, eval_msgs))
        msgs, scripts = zip(*res) if res else (None, None)
        assert len(msgs) == len(
            scripts
        ), f"(internal) 'msgs' and 'scripts' should be same length"
        self.last_uid = msgs[-1].uid
        self.msgs = msgs
        self.scripts = scripts

    def invoke(self, idx: int):
        msg: MailMessage = self.msgs[idx]
        script: ScriptConfig = self.scripts[idx]
        print(f"--> EXECUTE: {idx} msg: {msg.subject}, ---- script: {script}")
        try:
            assert os.path.isfile(
                script.exec_path
            ), f"failed to call script - path does not exist ({script.exec_path})"
            py_call = "python" if script.python_ver == 2 else "python3"
            res = subprocess.call([py_call, script.exec_path])
            logging.debug(f"script res: {res}")
            print()
        except Exception as e:
            logging.error(f"err during test invoke script: {e}")

    def eval_pattern(
        self, mail: MailMessage
    ) -> Tuple[MailMessage, ScriptConfig | None]:
        try:
            for script in self.config.scripts:
                res = script.get_pattern().match(mail.subject)
                if res:
                    logging.debug(f"eval: - subject: {mail.subject} - res: {res}")
                    return (mail, script)
            return (mail, None)
        except Exception as e:
            logging.error(f"fail during eval_mail: {e}")
            return None
