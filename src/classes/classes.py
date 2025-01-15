from dataclasses import dataclass

@dataclass
class MailServer:
    host: str
    port: str


@dataclass
class MailConfig:
    email: str
    pwd: str
    server: MailServer
