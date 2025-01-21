import logging
import datetime
import msgspec
from pathlib import Path
from src.classes import ScriptExecutionLog
from tinydb import TinyDB


class Storage:
  def __init__(self):
    dir = Path(".").resolve()
    self.filename = "storage.json"
    store_path = Path.joinpath(dir, self.filename)
    self.db = TinyDB(store_path)
    logging.debug(f"storage init {store_path=}")

  def add_log(self, subject: str, log: ScriptExecutionLog):
    try:
      time = datetime.datetime.now()
      log_key = f"[{time}|{subject}]"
      data = {log_key: log}
      json = msgspec.json.encode(data)
      self.db.insert(msgspec.json.decode(json))
      logging.debug(f"added log, {log_key=}")
    except Exception as e:
      logging.error(f"err during store_log: {e}")
