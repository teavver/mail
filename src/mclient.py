import logging
import subprocess
import threading
from datetime import datetime
from itertools import filterfalse
from subprocess import CalledProcessError
from typing import cast
from imap_tools import MailBox, MailboxLoginError, MailMessage
from src.interval import ThreadJob
from src.storage import Storage
from .classes import AppConfig, Defaults, ScriptConfig, ScriptExecutionLog


class MailClient:
  def __init__(self, config: AppConfig, storage: Storage):
    self.config = config
    self.db = storage
    self.mailbox: MailBox | None = None
    # history mode
    self.matches: list[tuple[MailMessage, ScriptConfig | None]] = []
    # polling mode
    self.is_polling: bool = False
    self.poll_event: threading.Event | None = None
    self.poll_thread: ThreadJob | None = None
    self.last_uid: int = -1
    # init polling thread
    if config.general.mode == "polling":
      self.poll_event = threading.Event()
      self.poll_thread = ThreadJob(lambda: self.__poll(), self.poll_event, self.config.general.polling_interval)
      logging.debug("init polling Thread ok")

  def __poll(self):
    """(mode: polling) continuously check for new emails & eval against patterns"""
    try:
      logging.debug("POLLING NEW STUFF")
    except Exception as e:
      logging.error(f"exception during poll: {e}")

  def __eval_pattern(self, mail: MailMessage) -> tuple[MailMessage, ScriptConfig | None]:
    try:
      for script in self.config.scripts:
        from_pattern = script.get_from_pattern()
        if from_pattern != Defaults.REGEXP_FROM and not from_pattern.match(mail.from_):
          logging.debug(f"MAIL SENDER NOT MATCH, expected: {from_pattern}, got: {mail.from_}")
          return (mail, None)
        src = mail.text if script.regexp_main_target == "body" else mail.subject
        res = script.get_main_pattern().match(src)
        if res:
          logging.debug(f"eval match: subject: {mail.subject}, target: {script.regexp_main_target}, res: {res}")
          return (mail, script)
      logging.debug(f"MAIN_REGEX NOT MATCH, expected: {src}")
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
    self.__poll()
    self.is_polling = True

  def fetch_inbox(self):
    """(mode: history) fetch last FETCH_LIMIT messages from mailbox & eval against patterns"""
    logging.debug(f"fetching inbox ({self.config.general.fetch_limit})")
    msgs_gen = (msg for msg in self.mailbox.fetch(limit=self.config.general.fetch_limit, reverse=True, charset="UTF-8"))
    eval_msgs = tuple([self.__eval_pattern(msg) for msg in msgs_gen])
    self.matches = list(filterfalse(lambda x: x is None or x[1] is None, eval_msgs))
    logging.debug(f"fetch_inbox matches count: {len(self.matches)}")

  def invoke_script(self, idx: int):
    assert self.matches[idx] is not None, "failed to invoke: no match with such idx"
    msg, script = cast(tuple[MailMessage, ScriptConfig], self.matches[idx])
    logging.debug("--- INVOKE START ---")
    logging.debug(f"{idx=}, {msg.subject=}, {script.exec_path=}")
    try:
      err_msg = None
      if script.exec_once and self.db.get_log(script.name, script.exec_path):
        return logging.debug("script is 'exec_once' and was already executed, aborting")
      res = subprocess.run(script.exec_path.split(" "), check=True)
      exec_time = datetime.now()
      log = ScriptExecutionLog(script.exec_path, exec_time, res.returncode)
      self.db.add_log(msg.subject, script.name, log)
      logging.debug(f"script res: {res}, invoke end time: {exec_time}")
      return
    except CalledProcessError as e:
      err_msg = f"CalledProcessError during invoke: {e}"
    except Exception as e:
      err_msg = f"Exception during invoke: {e}"
    logging.error(err_msg)
    log = ScriptExecutionLog(script.exec_path, datetime.now(), -1, err_msg)
    self.db.add_log(msg.subject, script.name, log)
    logging.debug("--- INVOKE END ---")

  def run_auto(self):
    for idx, _ in enumerate(self.matches):
      self.invoke_script(idx)
