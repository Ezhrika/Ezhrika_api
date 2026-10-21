from logging.config import fileConfig

from alembic import context
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy.engine import Connection

from app.db.base import Base
import app.models  # noqa: F401


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


# Проверка существующей схемы перед первым stamp без изменения таблиц и данных.
def check_initial_schema(connection: Connection) -> None:
    scripts = ScriptDirectory.from_config(config)
    if scripts.get_current_head() != "0001" or context.get_revision_argument() != "0001":
        raise CommandError("Schema adoption is only supported for the initial revision 0001.")
    migration_context = MigrationContext.configure(
        connection, opts={"compare_type": True, "compare_server_default": True},
    )
    differences = compare_metadata(migration_context, target_metadata)
    if differences:
        raise CommandError(
            f"Database schema differs from the initial migration ({len(differences)} changes). "
            "Stamp was not applied. Review the schema differences before proceeding."
        )


# Запуск миграций через переданное подключение или PostgreSQL из настроек проекта.
def run_with_connection(connection: Connection) -> None:
    if context.get_x_argument(as_dictionary=True).get("check_schema") == "true":
        check_initial_schema(connection)
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        run_with_connection(connection)
        return
    from app.db.session import get_engine

    with get_engine().begin() as connection:
        run_with_connection(connection)


# Генерация SQL для PostgreSQL без подключения к БД и чтения .env.
def run_migrations_offline() -> None:
    if context.get_x_argument(as_dictionary=True).get("check_schema") == "true":
        raise CommandError("Schema verification requires a database connection; omit --sql.")
    context.configure(
        dialect_name="postgresql",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
