import logging
import msgspec
from datetime import datetime
from pathlib import Path
from src.classes import ScriptExecutionLog, Log
from tinydb import TinyDB, Query


class Storage:
  def __init__(self):
    dir = Path(".").resolve()
    self.filename = "storage.json"
    store_path = Path.joinpath(dir, self.filename)
    self.db = TinyDB(store_path)
    logging.debug(f"storage init {store_path=}")

  def add_log(self, subject: str, script_name: str, log: ScriptExecutionLog):
    try:
      # TODO: check for existing matching s.name & subject and replace
      ts = datetime.now()
      data = Log(ts, script_name, subject, log)
      bjson = msgspec.json.encode(data)
      self.db.insert(msgspec.json.decode(bjson))
      logging.debug(f"added log, {data=}")
    except Exception as e:
      logging.error(f"err during store_log: {e}")

  def get_log(self, exec_query: str | datetime, exec_path: str):
    """search logs based on script Name or script execution Timestamp"""
    query_key = "ts" if isinstance(exec_query, datetime) else "script_name"
    logging.debug(f"get_log: {query_key=} , {exec_query=} , {exec_path=}")
    q1 = Query()[query_key] == exec_query
    q2 = Query()["log"]["exec_path"] == exec_path
    matches = self.db.search(q1 & q2)
    logging.debug(f"get_log matches: {matches}")
    return matches
