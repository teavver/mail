import argparse, sys, os, re, logging, msgspec
from dotenv import load_dotenv
from .classes import EnvConfig, AppConfig


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(levelname)s]: %(message)s",
    )
    if args.debug:
        logging.debug(f"args: {args}")
    return args


def get_env() -> EnvConfig:
    try:
        load_dotenv()
        required_env_keys = EnvConfig.__annotations__.keys()
        env = {key: os.getenv(key) for key in required_env_keys}
        env = EnvConfig(**env)
        return env
    except Exception as e:
        logging.error(f"fail during get_env: {e}")
        sys.exit(1)


def get_config() -> AppConfig:
    try:
        with open("config.toml", "rb") as f:
            config = msgspec.toml.decode(f.read(), type=AppConfig)
            logging.debug(f"config: {config}")
            return config
    except Exception as e:
        logging.error(f"err during parse_config: {e}")
        sys.exit(1)
    
    
# exp
def err(msg: str, method: str = "", exit = False):
    additional_info = f"err during {method}: " if method is not None else ""
    logging.error(f"{additional_info}{msg}")
    if exit: sys.exit(1)