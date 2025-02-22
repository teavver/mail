import logging
import signal
import sys
import threading
from timeit import default_timer as timer
import src.util as util
from src.classes import AppConfig, EnvConfig, AppArgs
from mail_client import MailClient
from src.storage import Storage


def main():
  env: EnvConfig = util.get_env()
  args: AppArgs = util.get_args()
  config: AppConfig = util.get_config(args)
  storage = Storage()
  mail = MailClient(config, storage, args)

  util.rotate_logs(args.logfile)
  login = env.LOGIN or config.mail.login
  pwd = env.PASSWORD or config.mail.password
  if any(cred is None for cred in [login, pwd]):
    logging.error("missing login credentials in .env or config.toml")
    sys.exit(1)

  mail.login(login, pwd)
  if mail is None:
    logging.error("mail login failed")
    sys.exit(1)

  def run_polling():
    signal.signal(signal.SIGINT, util.handle_quit)
    mail.start_polling()

  def run_history():
    s = timer()
    mail.fetch_inbox()
    e = timer()
    logging.debug(f"fetch took: {e - s}s")
    mail.run_auto()

  timeout = config.general.polling_timeout
  if timeout is not None and timeout > 0:
    logging.debug(f"setting up polling timeout, quitting in: {timeout}s")
    threading.Timer(timeout, mail.quit_polling).start()

  mode = config.general.run_mode
  logging.info(f"starting in {mode=} {'(forced)' if args.force_mode else ''}...")
  run = {"history": run_history, "polling": run_polling}
  if mode == "all":
    [func() for func in run.values()]
  else:
    run[mode]()


if __name__ == "__main__":
  main()
