import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
import msgspec
from msgspec import Meta, Struct

type RegexpTarget = Literal["title", "body"]

type AppMode = Literal["polling", "history"]


class Defaults:
  APP_MODE = "polling"
  LOGFILE = "log.txt"
  PYTHON_VER = 3
  REGEXP_FROM = ".*"
  REGEXP_TARGET = "title"
  FETCH_LIMIT = 50
  POLL_INTERVAL_SECONDS = 4


class EnvConfig(Struct):
  MAIL_ADDR: str
  MAIL_PWD: str


class MailHostConfig(Struct):
  host: str
  port: int


class ScriptConfig(Struct):
  # required
  name: Annotated[str, Meta(min_length=1)]
  exec_once: bool
  exec_path: Annotated[str, Meta(min_length=2)]
  regexp: Annotated[str, Meta(min_length=1)]
  # defaults
  regexp_from: Annotated[str, Meta(min_length=1)] = Defaults.REGEXP_FROM
  regexp_target: RegexpTarget = Defaults.REGEXP_TARGET
  python_ver: Literal[2, 3] = Defaults.PYTHON_VER
  # internal
  __from_pattern: re.Pattern | None = None  # compiled pattern from 'regexp_from'
  __main_pattern: re.Pattern | None = None  # compiled pattern from 'regexp'

  def __validate_regexp(self, regexp_val: str) -> re.Pattern:
    try:
      return re.compile(regexp_val)
    except Exception as e:
      logging.error(f"err during __validate_regexp: {regexp_val=}, err: {e}")
      sys.exit(1)

  def __post_init__(self):
    self.__main_pattern = self.__validate_regexp(self.regexp)
    self.__from_pattern = self.__validate_regexp(self.regexp_from)
    str_self = {
      **{k: getattr(self, k) for k in ["name", "exec_once", "exec_path", "regexp", "regexp_target", "python_ver"]},
      "__main_pattern": self.__main_pattern.pattern if self.__main_pattern else None,
      "__from_pattern": self.__from_pattern.pattern if self.__from_pattern else None,
    }
    logging.debug(f"Script '{self.name}': {json.dumps(msgspec.to_builtins(str_self), indent=2)}")

  def get_from_pattern(self):
    return self.__from_pattern

  def get_main_pattern(self):
    return self.__main_pattern


class ScriptExecutionLog(Struct):
  # absolute path of the script
  exec_path: str
  # timestamp when the script finished
  exec_ts: datetime
  # return value of subprocess.call()
  # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
  code: int
  # additional info, e.g. call error
  msg: str | None


class GeneralAppSettings(Struct):
  mode: AppMode = Defaults.APP_MODE
  fetch_limit: int = Defaults.FETCH_LIMIT
  polling_interval: int = Defaults.POLL_INTERVAL_SECONDS

  def __post_init__(self):
    logging.debug(f"general settings: {json.dumps(msgspec.to_builtins(self), indent=2)}")


class AppConfig(Struct):
  general: GeneralAppSettings
  mail: MailHostConfig
  scripts: list[ScriptConfig]


class AppArgs(Struct):
  debug: bool | None = False
  logfile: str | None = Defaults.LOGFILE


@dataclass
class MailClient:
  email: str
  pwd: str
  host: MailHostConfig


@dataclass
class Log:
  ts: str
  script_name: str
  subject: str
  log: ScriptExecutionLog
