from pathlib import Path

from dynaconf import Dynaconf

BASE_DIR = Path(__file__).resolve().parent.parent.parent

settings = Dynaconf(
    envvar_prefix="SIMPLE_RAG",
    environment=True,
    settings_files=[BASE_DIR / "settings.toml"],
    load_dotenv=True,
    env_switcher="SERVICE_ENV",
    dotenv_path=BASE_DIR / ".env",
)
