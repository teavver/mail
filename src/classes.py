import re
import sys
import json
import msgspec
import logging
from msgspec import Struct, Meta
from dataclasses import dataclass
from typing import Literal, Optional, Annotated

type RegexpTarget = Literal["title", "body"]


class Defaults:
  PYTHON_VER = 3
  REGEXP_TARGET = "title"
  FETCH_FULL = 500
  FETCH_RECENT = 50


# config related


class EnvConfig(Struct):
  MAIL_ADDR: str
  MAIL_PWD: str


class MailHostConfig(Struct):
  host: str
  port: int


class ScriptConfig(Struct):
  # mandatory
  name: Annotated[str, Meta(min_length=1)]
  exec_once: bool
  exec_path: Annotated[str, Meta(min_length=2)]
  regexp: Annotated[str, Meta(min_length=1)]
  # defaults
  regexp_target: RegexpTarget = Defaults.REGEXP_TARGET
  python_ver: Literal[2, 3] = Defaults.PYTHON_VER
  __pattern: Optional[re.Pattern] = None

  def __serialize(self):
    """TODO: override how msgspec serializes class instead of this garbage?"""
    data = msgspec.structs.asdict(self)
    print(data)
    data.pop("_ScriptConfig__pattern", None)
    data["__pattern"] = self.__pattern.pattern if self.__pattern else None
    return data

  def __validate_regexp(self) -> re.Pattern:
    try:
      return re.compile(self.regexp)
    except Exception as e:
      logging.error(f"err during __validate_regexp - {e}")
      sys.exit(1)

  def __post_init__(self):
    print(self)
    self.__pattern = self.__validate_regexp()
    logging.debug(f"Script '{self.name}':\n{json.dumps(self.__serialize(), indent=2)}")

  def get_pattern(self):
    return self.__pattern


class ScriptExecutionLog(Struct):
  exec_path: str
  # return value of subprocess.call()
  # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
  code: int | None
  # additional message regarding the execution process of the script
  msg: str | None


class GeneralAppSettings(Struct):
  fetch_full: int = Defaults.FETCH_FULL
  fetch_recent: int = Defaults.FETCH_RECENT


class AppConfig(Struct):
  general: GeneralAppSettings
  mail: MailHostConfig
  scripts: list[ScriptConfig]


# data


@dataclass
class MailClient:
  email: str
  pwd: str
  host: MailHostConfig
