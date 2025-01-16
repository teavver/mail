from dataclasses import dataclass

@dataclass
class MailHostConfig:
    server: str
    port: str


@dataclass
class MailConfig:
    email: str
    pwd: str
    host: MailHostConfig
