from setuptools import setup

setup(
  name="mail",
  version="0.0.1+dev",
  author="teavver",
  install_requires=["imap-tools", "msgspec", "python-dotenv", "tinydb"],
  python_requires=">=3.12",
  extras_require={
    "testing": ["pytest"],
    "linting": [
      "pre-commit",
      "ruff",
    ],
  },
)
