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


type ScriptMode = Literal["polling", "history"]


type AppRunMode = Literal["all"] | ScriptMode


class Defaults:
  # config-related
  APP_RUN_MODE = "all"
  LOGFILE = "log.txt"
  REGEXP_FROM = ".*"
  REGEXP_MAIN_TARGET = "title"
  FETCH_LIMIT = 50
  POLL_INTERVAL_SECONDS = 5
  POLL_TIMEOUT = 0
  # internal
  CONFIG_PATH = "config.toml"
  MAIL_LOGIN_TIMEOUT = 60


class EnvConfig(Struct):
  LOGIN: str | None = None
  PASSWORD: str | None = None


class MailBoxConfig(Struct):
  host: str
  port: int
  # allow storing credentials in config.toml instead of .env as fallback
  login: str | None = None
  password: str | None = None

  def __post_init__(self):
    logging.debug(f"mailbox config: {json.dumps(msgspec.to_builtins(self), indent=2)}")


class ScriptConfig(Struct):
  # required
  mode: ScriptMode
  name: Annotated[str, Meta(min_length=1)]
  exec_once: bool
  exec_path: Annotated[str, Meta(min_length=2)]
  regexp_main: Annotated[str, Meta(min_length=1)]
  # defaults
  regexp_from: Annotated[str, Meta(min_length=1)] = Defaults.REGEXP_FROM
  regexp_main_target: RegexpTarget = Defaults.REGEXP_MAIN_TARGET
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
    self.__main_pattern = self.__validate_regexp(self.regexp_main)
    self.__from_pattern = self.__validate_regexp(self.regexp_from)
    str_self = {
      **{
        k: getattr(self, k)
        for k in ["name", "exec_once", "exec_path", "regexp_main", "regexp_from", "regexp_main_target"]
      },
      "__main_pattern": self.__main_pattern.pattern if self.__main_pattern else None,
      "__from_pattern": self.__from_pattern.pattern if self.__from_pattern else None,
    }
    logging.debug(f"Script '{self.name}': {json.dumps(msgspec.to_builtins(str_self), indent=2)}")

  def get_from_pattern(self):
    return self.__from_pattern

  def get_main_pattern(self):
    return self.__main_pattern


class ScriptExecutionLog(Struct):
  # subject of mail that matched regexp_main
  mail_subject: str
  # abs path of the script
  exec_path: str
  # timestamp when the script exited
  exec_ts: datetime
  # from script conf
  exec_once: bool
  # main regexp from the script's config
  regexp_main: str
  # return code of subprocess.run()
  # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
  code: int
  # additional info: script's stderr + any errors that occurred while calling the script
  msgs: list[str] = []


class GeneralAppSettings(Struct):
  run_mode: AppRunMode
  fetch_limit: int = Defaults.FETCH_LIMIT
  polling_interval: int = Defaults.POLL_INTERVAL_SECONDS
  polling_timeout: Annotated[int, Meta(ge=0)] = Defaults.POLL_TIMEOUT

  def __post_init__(self):
    logging.debug(f"general settings: {json.dumps(msgspec.to_builtins(self), indent=2)}")


class AppConfig(Struct):
  general: GeneralAppSettings
  mail: MailBoxConfig
  scripts: list[ScriptConfig]


class AppArgs(Struct):
  debug: bool = False
  quiet: bool = False
  slow: bool = False
  logfile: str | None = Defaults.LOGFILE
  custom_config: str | None = None
  force_mode: AppRunMode | None = None


@dataclass
class MailClient:
  email: str
  pwd: str
  host: MailBoxConfig


@dataclass
class Log:
  ts: str
  script_name: str
  log: ScriptExecutionLog
