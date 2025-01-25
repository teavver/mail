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
  mail = MailClient(config, storage)
  mail.login(env.MAIL_ADDR, env.MAIL_PWD)
  assert mail is not None

  if mail is None:
    logging.error("mail login failed")
    sys.exit(1)

  mail.fetch_inbox("recent")
  logging.info("initial fetch complete")

  mail.run_auto()
  logging.info("done")


if __name__ == "__main__":
  main()
