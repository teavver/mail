import argparse
import logging
import os
import sys
import msgspec
from dotenv import load_dotenv
from .classes import AppArgs, AppConfig, Defaults, EnvConfig


def get_args() -> AppArgs:
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--debug", action="store_true")
  parser.add_argument("--logfile", type=str)
  # TODO: add:
  # --config FILEPATH
  # --quiet NO LOGS AT ALL
  args = parser.parse_args()
  logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(levelname)s [%(asctime)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(args.logfile or Defaults.LOGFILE, mode="a"), logging.StreamHandler()],
  )
  logging.debug(f"args: {args}")
  app_args = msgspec.convert(args.__dict__, AppArgs)
  return app_args


def get_env() -> EnvConfig:
  try:
    load_dotenv()
    required_env_keys = EnvConfig.__annotations__.keys()
    env = {key: os.getenv(key) for key in required_env_keys}
    return EnvConfig(**env)
  except Exception as e:
    logging.error(f"fail during get_env: {e}")
    sys.exit(1)


def get_config() -> AppConfig:
  try:
    with open("config.toml", "rb") as f:
      config = msgspec.toml.decode(f.read(), type=AppConfig)
      unique_names = len({s.name for s in config.scripts}) == len(config.scripts)
      if not unique_names:
        logging.error("script names must be unique")
        sys.exit(1)
      logging.debug(f"get_config load OK: {config}")
      return config
  except Exception as e:
    logging.error(f"err during parse_config: {e}")
    sys.exit(1)


def handle_quit(sig, frame):
  logging.info("quitting")
  sys.exit(0)
