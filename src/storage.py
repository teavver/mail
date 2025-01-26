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
    store_path = Path.joinpath(curdir, self.filename)
    self.db = TinyDB(store_path)
    logging.debug(f"storage init {store_path=}")

  def add_log(self, subject: str, script_name: str, log: ScriptExecutionLog):
    try:
      exists = self.db.contains(where("script_name") == script_name)
      ts = datetime.now()
      logging.debug(f"add_log call: ts: {ts} , exists: {exists}")
      log = Log(ts, script_name, subject, log)
      json = msgspec.to_builtins(log)
      if exists:
        self.db.update(json, where("script_name") == script_name)
      else:
        self.db.insert(json)
      logging.debug(f"{'updated' if exists else 'added'} log, obj: {json}")
    except Exception as e:
      logging.error(f"err during store_log: {e}")

  def get_log(self, exec_query: str | datetime, exec_path: str):
    """search logs based on script Name or script execution Timestamp"""
    query_key = "ts" if isinstance(exec_query, datetime) else "script_name"
    logging.debug(f"get_log: {query_key=} , {exec_query=} , {exec_path=}")
    q1 = where(query_key) == exec_query
    q2 = where("log")["exec_path"] == exec_path
    matches = self.db.search(q1 & q2)
    logging.debug(f"get_log matches: {matches}")
    return matches
