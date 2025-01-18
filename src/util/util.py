import argparse, sys, os, logging, re
from dotenv import load_dotenv


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-p", "--pattern", type=str, required=False)
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
    required_env_keys = [
        "MAIL_ADDR",
        "MAIL_PWD",
        "MAIL_HOST",
        "MAIL_PORT",
        "CALLBACK_NAME",
    ]
    env = {key: os.getenv(key) for key in required_env_keys}
    missing = [key for key, val in env.items() if val is None or val == ""]
    if missing:
        logging.error(f'Missing (or empty) env keys: {", ".join(missing)}')
        sys.exit(1)
    return env


def test_regex(reg: str):
    logging.debug(f"testing regex: '{reg}'")
    try:
        pattern = re.compile(reg)
        return pattern
    except Exception as e:
        logging.error(f"err when testing regex: {e}")
        return False
