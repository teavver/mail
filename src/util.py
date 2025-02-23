import argparse
import logging
import os
from pathlib import Path
import sys
import msgspec
import json
from logging import handlers
from msgspec import ValidationError
from dotenv import load_dotenv
from src.classes import AppArgs, AppConfig, Defaults, EnvConfig


def get_args() -> AppArgs:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="enable debug logging (affects only terminal output)"
  )
  parser.add_argument(
    "-q",
    "--quiet",
    action="store_true",
    default=False,
    help="log only errors to the terminal, does not affect logfile (ignores --debug value)",
  )
  parser.add_argument(
    "-s",
    "--slow",
    action="store_true",
    default=False,
    help="messages are fetched one by one. much lower memory consumption than normal, also much slower",
  )
  parser.add_argument(
    "-lf", "--logfile", default=None, type=str, help="use your own logfile instead of the default one"
  )
  parser.add_argument(
    "-cc",
    "--custom-config",
    default=None,
    type=str,
    help="use your own config.toml from a path. Overrides local config",
  )
  parser.add_argument(
    "-fm",
    "--force-mode",
    default=None,
    type=str,
    help="""
    force app mode regardless of what's set in your local or custom config. supported vals: all | polling | history
    """,
  )
  args = parser.parse_args()
  app_args = None
  try:
    app_args = msgspec.convert(args.__dict__, type=AppArgs)
  except ValidationError as e:
    logging.error(f"err during args validation: {e}")
    sys.exit(1)
  if app_args.logfile and not os.path.exists(app_args.logfile):
    logging.error("specified --logfile (-lf) path could not be resolved, does the file exist?")
    sys.exit(1)
  app_args.logfile = app_args.logfile or Defaults.LOGFILE
  log_level = logging.ERROR if app_args.quiet else logging.DEBUG if app_args.debug else logging.INFO
  logging.basicConfig(
    level=log_level,
    format="%(levelname)s [%(asctime)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[handlers.WatchedFileHandler(app_args.logfile), logging.StreamHandler()],
  )
  logging.debug(f"args: {json.dumps(args.__dict__, indent=2)}")
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


def get_config(args: AppArgs) -> AppConfig:
  directory = Path(__file__).resolve().parent.parent
  config_file = args.custom_config or Defaults.CONFIG_PATH
  config_path = Path.joinpath(directory, config_file)
  try:
    with open(config_path, "rb") as f:
      config = msgspec.toml.decode(f.read(), type=AppConfig)
      unique_names = len({s.name for s in config.scripts}) == len(config.scripts)
      if not unique_names:
        logging.error("script names must be unique")
        sys.exit(1)
      if args.force_mode is not None:
        config.general.run_mode = args.force_mode
      logging.debug(f"get_config load OK: {config}")
      return config
  except ValidationError as e:
    logging.error(f"err during config validation: {e}")
  except Exception as e:
    logging.error(f"err during parse_config: {e}")
  sys.exit(1)


def rotate_logs(logfile):
  old_log_filename = f"_old_{logfile}"
  num_lines = sum(1 for _ in open(logfile))
  if num_lines >= Defaults.MAX_LINES_LOGFILE:
    logging.debug("rotating logfile")
    os.rename(logfile, old_log_filename)


def handle_quit(sig, frame):
  logging.info("quitting")
  sys.exit(0)
