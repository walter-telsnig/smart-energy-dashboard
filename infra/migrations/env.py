# Alembic environment — points to the one true Base + imports ORM so metadata is populated.

from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool

# Ensure repo root is on sys.path (robust on Windows/OneDrive paths)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.settings import settings
from infra.db import Base
# import infra.accounts.orm  # noqa: F401  (registers UserORM on Base)
import modules.accounts.model  # noqa: F401 (registers Account on Base)

# Alembic Config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.db_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(settings.db_url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
