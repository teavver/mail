import sys
import logging
import subprocess
import threading
from datetime import datetime
from itertools import filterfalse
from subprocess import CalledProcessError
from imap_tools import MailBox, MailboxLoginError, MailMessage
from src.interval import ThreadJob
from src.storage import Storage
from .classes import AppConfig, Defaults, ScriptConfig, ScriptExecutionLog, ScriptMode, AppArgs


class MailClient:
  def __init__(self, config: AppConfig, storage: Storage, args: AppArgs):
    self.config = config
    self.db = storage
    self.mailbox: MailBox | None = None
    self.app_args = args
    # history mode
    self.matches: list[tuple[MailMessage, ScriptConfig | None]] = []
    # polling mode
    self.last_uid: int = -1
    # TODO: tweak poll_limit, temp solution here
    self.poll_limit = round(self.config.general.polling_interval * 0.02) + 2
    self.poll_event: threading.Event | None = None
    self.poll_thread: ThreadJob | None = None
    self.is_polling: bool = False
    # init polling thread
    if any(script.mode == "polling" for script in self.config.scripts):
      self.poll_event = threading.Event()
      self.poll_thread = ThreadJob(lambda: self.__poll(), self.poll_event, self.config.general.polling_interval)
      logging.debug(f"init polling thread ok. poll limit: {self.poll_limit}")

  def __poll(self):
    """(mode: polling) continuously check for new emails & eval against patterns"""
    try:
      msgs_gen = (msg for msg in self.mailbox.fetch(limit=self.poll_limit, charset="UTF-8", reverse=True, bulk=True))
      last_msg: MailMessage = max(list(msgs_gen), key=lambda msg: int(msg.uid))
      if self.last_uid is not -1 and last_msg.uid != self.last_uid:
        (msg, script) = self.__eval_pattern(last_msg, "polling")
        if script is None:
          return logging.debug("poll got msg but no match")
        logging.debug(f"poll got new match: {msg.subject=}, {msg.uid=}")
        self.invoke_script(msg, script)
      self.last_uid = last_msg.uid
    except Exception as e:
      logging.error(f"exception during poll: {e}")

  def __eval_pattern(self, msg: MailMessage, mode: ScriptMode | None = None) -> tuple[MailMessage, ScriptConfig | None]:
    try:
      for script in self.config.scripts:
        if mode is not None and script.mode != mode:
          return (msg, None)
        from_pattern = script.get_from_pattern()
        if from_pattern != Defaults.REGEXP_FROM and not from_pattern.match(msg.from_):
          logging.debug(f"msg.from did not match, expected: {from_pattern}, got: {msg.from_}")
          return (msg, None)
        src = msg.text if script.regexp_main_target == "body" else msg.subject
        res = script.get_main_pattern().match(src)
        if res:
          logging.debug(f"eval match: subject: {msg.subject}, target: {script.regexp_main_target}, res: {res}")
          return (msg, script)
      logging.debug(f"eval main regex did not match, subject: '{msg.subject}'")
      return (msg, None)
    except Exception as e:
      logging.error(f"fail during __eval_pattern: {e}")

  def login(self, login, pwd) -> MailBox | None:
    logging.info(f"logging in ({login=})...")
    try:
      mail = MailBox(self.config.mail.host, self.config.mail.port, Defaults.MAIL_LOGIN_TIMEOUT).login(login, pwd)
      self.mailbox = mail
      logging.info("mailbox login success")
      return mail
    except MailboxLoginError as e:
      logging.error(f"mailbox login err: {e}")
    except Exception as e:
      logging.error(f"mailbox login unknown err: {e}")
    sys.exit(1)

  def quit_polling(self):
    self.stop_polling()
    self.poll_event.set()
    logging.debug("quitting (polling mode timeout)")
    sys.exit(0)

  def stop_polling(self):
    if not self.is_polling:
      return logging.debug("stop_polling called when already off")
    logging.debug("stop_polling")
    self.poll_thread.pause()
    self.is_polling = False

  def start_polling(self):
    if self.is_polling:
      return logging.debug("start_polling called when already polling")
    if not any(script.mode == "polling" for script in self.config.scripts):
      return logging.debug("start_polling ignored - no polling scripts in config")
    logging.debug("start_polling")
    self.poll_thread.start()
    self.__poll()
    self.is_polling = True

  def fetch_inbox(self):
    """(mode: history) fetch last FETCH_LIMIT messages from mailbox & eval against patterns"""
    if not any(script.mode == "history" for script in self.config.scripts):
      return logging.debug(
        f"app mode is '{self.config.general.run_mode}' but no history scripts found, skipping fetch_inbox"
      )
    logging.debug(f"fetching inbox ({self.config.general.fetch_limit})")
    msgs_gen = (
      msg
      for msg in self.mailbox.fetch(
        limit=self.config.general.fetch_limit, reverse=True, charset="UTF-8", bulk=(not self.app_args.slow)
      )
    )
    eval_msgs = tuple([self.__eval_pattern(msg, "history") for msg in msgs_gen])
    self.matches = list(filterfalse(lambda x: x is None or x[1] is None, eval_msgs))
    logging.debug(f"fetch_inbox match count: {len(self.matches)}")

  def invoke_script(self, msg: MailMessage, script: ScriptConfig | None):
    if script is None:
      return
    logging.debug("--- INVOKE START ---")
    logging.debug(f"{msg.subject=}, {script.exec_path=}")
    try:
      err_msg = None
      if script.exec_once and self.db.get_log(script.name, script.exec_path):
        return logging.debug("script is 'exec_once' and was already executed, aborting")
      res = subprocess.run(script.exec_path.split(" "), check=True)
      exec_time = datetime.now()
      log = ScriptExecutionLog(script.exec_path, exec_time, res.returncode)
      self.db.add_log(msg.subject, script.name, log)
      logging.debug(f"script res: {res}, invoke end time: {exec_time}")
      logging.debug("--- INVOKE END ---")
      return
    except CalledProcessError as e:
      err_msg = f"CalledProcessError during invoke: {e}"
    except Exception as e:
      err_msg = f"Exception during invoke: {e}"
    logging.error(err_msg)
    log = ScriptExecutionLog(script.exec_path, datetime.now(), -1, err_msg)
    self.db.add_log(msg.subject, script.name, log)
    logging.debug("--- INVOKE END (ERR) ---")

  def run_auto(self):
    [self.invoke_script(msg, script) for msg, script in self.matches]
