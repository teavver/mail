import logging
import sys
import src.util as util
from src.classes import EnvConfig, AppConfig
from src.mclient import MailClient
from src.storage import Storage


def main():
  env: EnvConfig = util.get_env()
  util.get_args()
  config: AppConfig = util.get_config()
  storage = Storage()
  mclient = MailClient(config, storage)
  mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)
  assert mailbox is not None

  if mailbox is None:
    logging.error("mailbox login failed")
    sys.exit(1)

  mclient.fetch_inbox("recent")
  logging.info("initial fetch complete")

  mclient.run_auto()
  logging.info("done")


if __name__ == "__main__":
  main()
