import logging
import signal
import sys
import src.util as util
from src.classes import AppConfig, EnvConfig
from src.mclient import MailClient
from src.storage import Storage


def main():
  env: EnvConfig = util.get_env()
  util.get_args()
  config: AppConfig = util.get_config()
  storage = Storage()
  mail = MailClient(config, storage)
  mail.login(env.MAIL_ADDR, env.MAIL_PWD)
  if mail is None:
    logging.error("mail login failed")
    sys.exit(1)

  mode = config.general.mode
  logging.debug(f"starting in {mode=} ...")
  if mode == "polling":
    signal.signal(signal.SIGINT, util.handle_quit)
    mail.start_polling()
  else:
    mail.fetch_inbox()
    mail.run_auto()
    logging.info("done")


if __name__ == "__main__":
  main()
