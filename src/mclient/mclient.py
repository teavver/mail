import threading, logging
from typing import Literal

# TEMP CONFIG
FETCH_RECENT = 50
FETCH_MAX = 500

type MailFetchMode = Literal["recent", "all"]


class MailClient:
    def __init__(self, mail, pattern):
        self.mail = mail
        self.pattern = pattern
        self.last_email_id = None
        self.all_email_ids = []
        self.lock = threading.Lock()

    def fetch_inbox(self, mode: MailFetchMode):
        limit = FETCH_MAX if mode == "all" else FETCH_RECENT
        msgs_gen = (msg for msg in self.mail.fetch(limit=limit, reverse=True, charset="UTF-8"))
        return list(msgs_gen)

    def check_for_existing_emails(self):
        pass
