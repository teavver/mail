import logging
import src.util as util
from src.classes import MailClient, EnvConfig, AppConfig
from src.mclient import MailClient
from src.interactive import InteractiveMode


def main():
    env: EnvConfig = util.get_env()
    args = util.get_args()
    config: AppConfig = util.get_config()
    mclient = MailClient(config)
    mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)
    logging.info(mailbox.login_result)

    mclient.fetch_inbox("recent")
    logging.info("initial fetch complete")

    # interactive mode
    if args.interactive:
        logging.info(f"starting interactive mode...")
        im = InteractiveMode(mclient.msgs, mclient.handlers)
        im.run()

    # TODO: handlers -> scripts
    # regex -> regexp
    logging.info("auto mode")


if __name__ == "__main__":
    main()
