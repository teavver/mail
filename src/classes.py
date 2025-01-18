from msgspec import Struct
from dataclasses import dataclass
from typing import Literal


class Defaults:
    PYTHON_VER = 3
    PATTERN_TYPE = "title"
    FETCH_FULL = 500
    FETCH_RECENT = 50


# config related


class EnvConfig(Struct):
    MAIL_ADDR: str
    MAIL_PWD: str


class MailHostConfig(Struct):
    host: str
    port: int


class CallbackHandlerConfig(Struct):
    name: str  # folder name for lookup, must match
    pattern: str
    exec_once: bool
    pattern_type: Literal["title", "body"] = Defaults.PATTERN_TYPE
    python_ver: Literal[2, 3] = Defaults.PYTHON_VER


class GeneralAppSettings(Struct):
    fetch_full: int = Defaults.FETCH_FULL
    fetch_recent: int = Defaults.FETCH_RECENT


class AppConfig(Struct):
    general: GeneralAppSettings
    mail: MailHostConfig
    handlers: list[CallbackHandlerConfig]


# mail


@dataclass
class MailClient:
    email: str
    pwd: str
    host: MailHostConfig
