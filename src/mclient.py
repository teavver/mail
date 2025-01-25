import logging
import subprocess
import os
from datetime import datetime
from subprocess import CalledProcessError
from .classes import AppConfig, ScriptConfig, ScriptExecutionLog, Defaults
from typing import Literal, Tuple, cast
from imap_tools import MailBox, MailMessage, MailboxLoginError
from itertools import filterfalse
from src.storage import Storage


class MailClient:
  def __init__(self, config: AppConfig, storage: Storage):
    self.config = config
    self.db = storage
    self.mailbox: MailBox | None = None
    self.last_uid: int | None = None
    self.matches = []

  def __eval_pattern(self, mail: MailMessage) -> Tuple[MailMessage, ScriptConfig | None]:
    try:
      for script in self.config.scripts:
        from_pattern = script.get_from_pattern()
        if from_pattern != Defaults.REGEXP_FROM and not from_pattern.match(mail.from_):
          logging.debug(f"MAIL SENDER NOT MATCH, expected: {from_pattern}, got: {mail.from_}")
          return (mail, None)
        src = mail.text if script.regexp_target == "body" else mail.subject
        res = script.get_main_pattern().match(src)
        if res:
          logging.debug(f"eval match: subject: {mail.subject}, target: {script.regexp_target}, res: {res}")
          return (mail, script)
      return (mail, None)
    except Exception as e:
      logging.error(f"fail during eval_mail: {e}")

  def login(self, login, pwd) -> MailBox:
    try:
      mail = MailBox(self.config.mail.host, self.config.mail.port, 60).login(login, pwd)
      self.mailbox = mail
      logging.info("mailbox login success")
      return mail
    except MailboxLoginError as e:
      logging.error(f"mailbox login err: {e}")
    except Exception as e:
      logging.error(f"mailbox login unknown err: {e}")

  def fetch_inbox(self, mode: Literal["recent", "full"]):
    limit = self.config.general.fetch_full if mode == "full" else self.config.general.fetch_recent
    msgs_gen = (msg for msg in self.mailbox.fetch(limit=limit, reverse=True, charset="UTF-8"))
    eval_msgs = tuple([self.__eval_pattern(msg) for msg in msgs_gen])
    self.matches = list(filterfalse(lambda x: x is None or x[1] is None, eval_msgs))
    logging.debug(f"fetch_inbox matches count: {len(self.matches)}")
    if self.matches:
      self.last_uid = self.matches[-1][0].uid

  def invoke_script(self, idx: int):
    msg, script = cast(tuple[MailMessage, ScriptConfig], self.matches[idx])
    logging.debug("--- INVOKE START ---")
    logging.debug(f"{idx=}, {msg.subject=}, {script.exec_path=}")
    try:
      assert os.path.isfile(script.exec_path), f"failed to call script - path does not exist ({script.exec_path=})"
      if script.exec_once and self.db.get_log(script.name, script.exec_path):
        return logging.debug("script is 'exec_once' and was already executed, aborting")
      # TODO: add more flexible call - custom full exec path?
      py_call = "python" if script.python_ver == 2 else "python3"
      res = subprocess.call([py_call, script.exec_path])
      exec_time = datetime.now()
      log = ScriptExecutionLog(script.exec_path, exec_time, res)
      self.db.add_log(msg.subject, script.name, log)
      logging.debug(f"script res: {res}, invoke end time: {exec_time}")
    except CalledProcessError as e:
      logging.error(f"CalledProcessError during invoke: {e}")
    except Exception as e:
      logging.error(f"Exception during invoke script: {e}")
    logging.debug("--- INVOKE END ---")

  def run_auto(self):
    for idx, _ in enumerate(self.matches):
      self.invoke_script(idx)
