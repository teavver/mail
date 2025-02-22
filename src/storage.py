import logging
from datetime import datetime
from pathlib import Path
import msgspec
from tinydb import TinyDB, where
from src.classes import Log, ScriptExecutionLog


class Storage:
  def __init__(self):
    curdir = Path(".").resolve()
    self.filename = "storage.json"
    self.q_property = "mail_subject"
    store_path = Path.joinpath(curdir, self.filename)
    self.db = TinyDB(store_path)
    logging.debug(f"storage init {store_path=}")

  def add_log(self, script_name: str, log: ScriptExecutionLog):
    try:
      exists = self.db.contains(where("log")[self.q_property] == log.mail_subject)
      ts = datetime.now()
      logging.debug(f"add_log call: ts: {ts} , exists: {exists}")
      db_log = Log(ts, script_name, log)
      json = msgspec.to_builtins(db_log)
      if exists:
        self.db.update(json, where("log")[self.q_property] == log.mail_subject)
      else:
        self.db.insert(json)
      logging.debug(f"{'updated' if exists else 'added'} log, obj: {json}")
    except Exception as e:
      logging.error(f"err during store_log: {e}")

  def log_exists(self, script_name: str, mail_subject: str) -> bool:
    logging.debug(f"get_log, query: {script_name=}, {mail_subject=}")
    q1 = where(self.q_property) == mail_subject
    q2 = where("script_name") == script_name
    matches = self.db.search(q1 & q2)
    logging.debug(f"get_log matches: {matches}")
    return len(matches) > 0
