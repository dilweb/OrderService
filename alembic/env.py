from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine.url import make_url

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
for path in (BASE_DIR, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from src.db.base import Base
from src.users.models.user import User  # noqa: F401 ensures metadata is registered

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _ensure_sync_url() -> str:
    raw_url = config.get_main_option("sqlalchemy.url")
    if not raw_url:
        raise RuntimeError("sqlalchemy.url is not configured")

    url = make_url(raw_url)
    drivername = url.drivername
    if "+" in drivername:
        sync_driver = drivername.split("+", 1)[0]
        url = url.set(drivername=sync_driver)
    return url.render_as_string(hide_password=False)


SYNC_DB_URL = _ensure_sync_url()
config.set_main_option("sqlalchemy.url", SYNC_DB_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=SYNC_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using synchronous engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
 