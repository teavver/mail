from msgspec import Struct
from dataclasses import dataclass
from typing import Literal

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
    pattern_type: Literal["title", "body"] = "title"
    python_ver: Literal[2, 3] = 3


class GeneralAppSettings(Struct):
    fetch_full: int = 500
    fetch_recent: int = 50


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
