import logging
import sys
import datetime
import src.util as util
from src.classes import EnvConfig, AppConfig, ScriptExecutionLog
from src.mclient import MailClient
from src.storage import Storage


def main():
  env: EnvConfig = util.get_env()
  util.get_args()
  config: AppConfig = util.get_config()
  mclient = MailClient(config)
  mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)

  if mailbox is None:
    logging.error("mailbox login failed")
    sys.exit(1)

  # mclient.fetch_inbox("recent")
  # logging.info("initial fetch complete")

  # mclient.run_auto()

  ts = datetime.datetime.now()
  script = config.scripts[0]
  log = ScriptExecutionLog(script.exec_path, ts, 0, "Storage TEST")
  store = Storage()

  store.add_log("Test", script.name, log)

  store.get_log(script.name)
  logging.info("done")


if __name__ == "__main__":
  main()
