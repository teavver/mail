import logging, sys
import src.util as util
from src.classes import MailClient, EnvConfig, AppConfig
from src.mclient import MailClient


def main():
    env: EnvConfig = util.get_env()
    args = util.get_args()
    config: AppConfig = util.get_config()
    mclient = MailClient(config)
    mailbox = mclient.login(env.MAIL_ADDR, env.MAIL_PWD)
    
    if mailbox is None:
        logging.error("mailbox login failed")
        sys.exit(1)

    mclient.fetch_inbox("recent")
    logging.info("initial fetch complete")
    
    mclient.run_auto()
    logging.info("done")
    


if __name__ == "__main__":
    main()
