import logging
import subprocess
import os
import threading
from datetime import datetime
from subprocess import CalledProcessError
from .classes import AppConfig, ScriptConfig, ScriptExecutionLog, Defaults
from typing import List, Tuple, cast
from imap_tools import MailBox, MailMessage, MailboxLoginError
from itertools import filterfalse
from src.interval import ThreadJob
from src.storage import Storage


class MailClient:
  def __init__(self, config: AppConfig, storage: Storage):
    self.config = config
    self.db = storage
    self.mailbox: MailBox | None = None
    # history mode
    self.matches: List[Tuple[MailMessage, ScriptConfig | None]] = []
    # polling mode
    # self.is_polling: bool = False
    self.poll_event: threading.Event | None = None
    self.poll_thread: ThreadJob | None = None
    self.last_uid: int = -1
    if config.general.mode == "polling":
      SECONDS = 3  # TODO CONFIG
      self.poll_event = threading.Event()
      self.poll_thread = ThreadJob(lambda: self.__poll(), self.poll_event, SECONDS)
      logging.debug("init polling Thread ok")

  def __poll(self):
    """(polling) continuously check for new messages & eval against pattenrs"""
    try:
      logging.debug("POLLING NEW STUFF")
    except Exception as e:
      logging.error(f"exception during poll: {e}")

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

  def pause_polling(self):
    if not self.is_polling:
      return logging.debug("pause_polling called when already off")
    logging.debug("pause_polling")
    self.poll_thread.pause()
    self.is_polling = False

  def start_polling(self):
    if self.is_polling:
      return logging.debug("start_polling called when already polling")
    logging.debug("start_polling")
    self.poll_thread.start()
    self.is_polling = True

  def fetch_inbox(self):
    """(history) fetch last FETCH_LIMIT messages from mailbox & eval against patterns"""
    msgs_gen = (msg for msg in self.mailbox.fetch(self.config.general.fetch_limit, reverse=True, charset="UTF-8"))
    eval_msgs = tuple([self.__eval_pattern(msg) for msg in msgs_gen])
    self.matches = list(filterfalse(lambda x: x is None or x[1] is None, eval_msgs))
    logging.debug(f"fetch_inbox matches count: {len(self.matches)}")

  def invoke_script(self, idx: int):
    assert self.matches[idx] is not None, "failed to invoke_script: no match with such idx"
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
