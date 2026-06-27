import os
from pathlib import Path

from dotenv import load_dotenv

from src.lib.config import Setting


def load_env(root: Path) -> None:
    """Populate os.environ from <root>/.env. Missing file is fine.

    override=False so a variable already present in the real environment
    wins over the .env file.
    """
    load_dotenv(dotenv_path=root / ".env", override=False)


def resolve(cli_value, setting: Setting) -> str:
    """CLI value > env var > built-in default. Returns a string path/value."""
    if cli_value is not None:
        return str(cli_value)
    env_value = os.environ.get(setting.env)
    if env_value:
        return env_value
    return setting.default
