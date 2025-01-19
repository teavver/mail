import re, sys, json, msgspec, logging
from msgspec import Struct, Meta
from dataclasses import dataclass
from typing import Literal, Optional, Annotated

type RegexTarget = Literal["title", "body"]


class Defaults:
    PYTHON_VER = 3
    REGEX_TYPE = "title"
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
    name: Annotated[str, Meta(min_length=1)]
    exec_once: bool
    exec_path: Annotated[str, Meta(min_length=2)]
    regex: Annotated[str, Meta(min_length=1)]
    regex_target: RegexTarget = Defaults.REGEX_TYPE  # TODO ADD THIS
    python_ver: Literal[2, 3] = Defaults.PYTHON_VER
    __pattern: Optional[re.Pattern] = None

    def __serialize(self):
        """TODO: override how msgspec serializes class instead of this garbage?"""
        data = msgspec.structs.asdict(self)
        data.pop("_CallbackHandlerConfig__pattern", None)
        data["__pattern"] = self.__pattern.pattern if self.__pattern else None
        return data

    def __validate_regex(self) -> re.Pattern:
        try:
            return re.compile(self.regex)
        except Exception as e:
            logging.error(f"err during __validate_regex - {e}")
            sys.exit(1)

    def __post_init__(self):
        self.__pattern = self.__validate_regex()
        logging.debug(
            f"Callback '{self.name}':\n{json.dumps(self.__serialize(), indent=2)}"
        )

    def get_pattern(self):
        return self.__pattern


class GeneralAppSettings(Struct):
    fetch_full: int = Defaults.FETCH_FULL
    fetch_recent: int = Defaults.FETCH_RECENT


class AppConfig(Struct):
    general: GeneralAppSettings
    mail: MailHostConfig
    handlers: list[CallbackHandlerConfig]


# data


@dataclass
class MailClient:
    email: str
    pwd: str
    host: MailHostConfig
