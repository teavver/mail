import argparse, sys, os, logging
from dotenv import load_dotenv


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-r", "--regex", type=str, required=True)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(levelname)s]: %(message)s",
    )
    if args.debug:
        logging.debug(f"Args: {args}")
    return args


def get_env():
    load_dotenv()
    required_env_keys = ["MAIL_ADDR", "MAIL_PWD", "MAIL_SERVER", "MAIL_PORT"]
    env = {key: os.getenv(key) for key in required_env_keys}
    missing = [key for key, val in env.items() if val is None or val is ""]
    if missing:
        logging.error(f'Missing (or empty) env keys: {", ".join(missing)}')
        sys.exit(1)
    return env
