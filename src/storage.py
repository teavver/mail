import os
import logging
from pathlib import Path


class Storage:
  def __init__(self):
    dir = Path(".").resolve()
    self.filename = "storage.json"
    logging.debug(f"Storage init {dir=}")

    # initialize storage file if needed
    store_path = Path.joinpath(dir, self.filename)
    logging.debug(store_path)
    if not Path.exists(store_path):
      self.__touch(store_path)
      logging.debug("storage file initialized (first launch)")

  def __touch(self, path: str):
    with open(path, "a"):
      os.utime(path, None)
