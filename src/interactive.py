import os, sys, termios, tty, time, logging
from typing import List
from rich.console import Console
from rich.table import Table
from imap_tools import MailMessage
from src.classes import CallbackHandlerConfig
from enum import Enum


class Keyboard:
    def __init__(self):
        self.supported_keys = Enum("supported_keys", {"Q": "q", "H": "h", "L": "l"})

    def is_key_supported(self, key):
        # return key in {k.value for k in self.supported_keys}
        return key in (member.value for member in self.supported_keys)

    # https://stackoverflow.com/a/72825322
    def getch(self):
        fd = sys.stdin.fileno()
        orig = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)  # or tty.setraw(fd) if you prefer raw mode's behavior.
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, orig)


# TODO: add legend bar at bottom,
# TODO: test pages etc.
class InteractiveMode:
    def __init__(self, msgs: List[MailMessage], handlers: List[CallbackHandlerConfig]):
        self.msgs = msgs
        self.handlers = handlers
        self.page = 1
        self.page_size = 10
        self.total_pages = (len(self.handlers) + self.page_size - 1) // self.page_size
        self.console = Console()
        self.kb = Keyboard()

    def __clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def __display_page(self):
        start_index = (self.page - 1) * self.page_size
        end_index = min(start_index + self.page_size, len(self.msgs))

        table = Table(title=f"Page {self.page}/{self.total_pages}")
        table.add_column("Subject", justify="left")
        table.add_column("Handler", justify="left")
        for i in range(start_index, end_index):
            table.add_row(self.msgs[i].subject, self.handlers[i].exec_path)
        self.console.print(table)

    def run(self):
        while True:
            self.__clear()
            self.__display_page()
            c = self.kb.getch()
            if self.kb.is_key_supported(c):
                match c:
                    # QUIT (q)
                    case self.kb.supported_keys.Q.value:
                        logging.info(f"exit (Q) called")
                        break
                    # LEFT (h)
                    case self.kb.supported_keys.H.value:
                        if self.page > 1:
                            self.page -= 1
                            self.__display_page()
                            time.sleep(0.1)
                    # RIGHT (l)
                    case self.kb.supported_keys.L.value:
                        if self.page != self.total_pages:
                            self.page += 1
                            self.__display_page()
                            time.sleep(0.1)
            time.sleep(0.1)
