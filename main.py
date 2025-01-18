import threading, logging, os, sys, subprocess
from imap_tools import MailBox, MailboxLoginError
from src.interval import ThreadJob
from src.classes import MailClient, MailHostConfig, EnvConfig
from src.mclient import MailClient
import src.util as util


def callback(name: str, arg: str):
    try:
        res = subprocess.call(["python", name, f"{arg}"])
        print(res)
    except Exception as e:
        logging.error(f"err during call_proc: {e}")


def main():
    env = util.get_env()
    args = util.get_args()
    config = util.get_config()
    
    patterns = [util.validate_regexp(h.pattern) for h in config.handlers]
    
    # mclient = MailClient(config, patterns)
    mclient = MailClient(config, patterns)
    mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)
    logging.info(mailbox.login_result)
    mclient.fetch_inbox("recent")
    return
    
    # msgs = mail_checker.fetch_inbox(config["general"])
    # for msg in matching:
    #     print(f"matching msg: ({msg.date_str}): {msg.subject}")
    # callback(env["CALLBACK_NAME"], matching[0].subject)
        
    # event = threading.Event()    
    # for msg in msgs:
    #     match = valid_pattern.match(msg.subject)
    #     print(f"match: {match}")
    # logging.debug(f"matching mails: {matching}")

    # try:
    #     k = ThreadJob(lambda: mail_checker.check_for_new_emails(), event, 5)
    #     k.start()
    #     logging.info("- run app ok")


if __name__ == "__main__":
    main()
