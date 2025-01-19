import logging, os, sys, subprocess
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
    mclient = MailClient(config)
    
    mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)
    logging.info(mailbox.login_result)
    mclient.fetch_inbox("recent")

if __name__ == "__main__":
    main()
