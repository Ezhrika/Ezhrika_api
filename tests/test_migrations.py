import ast
import io
import shutil
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.util import CommandError
from sqlalchemy import DefaultClause, create_engine, event, inspect, select, text

from app.db.base import Base
from app.models.user import User


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Проверка миграций на временной БД без чтения .env и доступа к локальной PostgreSQL.
class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # SQLite сравнивает пустой TEXT-default как SQL-строку, PostgreSQL — по значению.
        cls.original_defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and isinstance(default.arg, str) and default.arg == "":
                    cls.original_defaults.append((column, default))
                    column.server_default = DefaultClause(text("''"))

    @classmethod
    def tearDownClass(cls):
        for column, original_default in cls.original_defaults:
            column.server_default = original_default

    def setUp(self):
        self.enterContext(patch("logging.config.fileConfig"))
        self.engine = create_engine("sqlite://")
        self.addCleanup(self.engine.dispose)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    def config(self, connection=None, verify_schema=False):
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        if connection is not None:
            config.attributes["connection"] = connection
        config.cmd_opts = Namespace(x=["check_schema=true"] if verify_schema else [])
        return config

    def add_user(self, connection):
        connection.execute(User.__table__.insert().values(
            email="keep@example.org", role="student", password_hash="test-hash",
        ))

    def test_initial_upgrade_matches_models_and_is_repeatable(self):
        with self.engine.begin() as connection:
            config = self.config(connection)
            command.upgrade(config, "head")
            self.assertEqual(set(inspect(connection).get_table_names()), set(Base.metadata.tables) | {"alembic_version"})
            context = MigrationContext.configure(connection, opts={
                "compare_type": True, "compare_server_default": True,
            })
            self.assertEqual(compare_metadata(context, Base.metadata), [])
            self.add_user(connection)
            command.upgrade(config, "head")
            self.assertEqual(connection.scalar(select(User.email)), "keep@example.org")
            self.assertEqual(context.get_current_revision(), "0001")
            command.check(config)

    def test_existing_database_stamp_preserves_data(self):
        with self.engine.begin() as connection:
            Base.metadata.create_all(connection)
            self.add_user(connection)
            command.stamp(self.config(connection, verify_schema=True), "0001")
        with self.engine.connect() as connection:
            self.assertEqual(MigrationContext.configure(connection).get_current_revision(), "0001")
            self.assertEqual(connection.scalar(select(User.email)), "keep@example.org")

    def test_schema_mismatch_refuses_stamp_without_changing_data(self):
        with self.engine.begin() as connection:
            Base.metadata.create_all(connection)
            self.add_user(connection)
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN legacy_field VARCHAR(20)")
            with self.assertRaisesRegex(CommandError, "Database schema differs"):
                command.stamp(self.config(connection, verify_schema=True), "0001")
            self.assertFalse(inspect(connection).has_table("alembic_version"))
            self.assertEqual(connection.scalar(select(User.email)), "keep@example.org")

    def test_empty_database_cannot_be_stamped_with_schema_check(self):
        with self.engine.begin() as connection:
            with self.assertRaisesRegex(CommandError, "Database schema differs"):
                command.stamp(self.config(connection, verify_schema=True), "0001")
            self.assertEqual(inspect(connection).get_table_names(), [])

    def test_downgrade_then_upgrade_restores_schema(self):
        with self.engine.begin() as connection:
            config = self.config(connection)
            command.upgrade(config, "head")
            command.downgrade(config, "base")
            self.assertEqual(inspect(connection).get_table_names(), ["alembic_version"])
            command.upgrade(config, "head")
            self.assertEqual(MigrationContext.configure(connection).get_current_revision(), "0001")

    def test_offline_sql_targets_postgresql(self):
        output = io.StringIO()
        config = self.config()
        config.output_buffer = output
        command.upgrade(config, "head", sql=True)
        sql = output.getvalue()
        for table_name in Base.metadata.tables:
            self.assertIn(f"CREATE TABLE {table_name}", sql)
        self.assertIn("TIMESTAMP WITH TIME ZONE", sql)
        self.assertIn("SERIAL", sql)
        self.assertIn("COMMIT;", sql)

    def test_revision_template_generates_runnable_autogenerated_migration(self):
        with tempfile.TemporaryDirectory(prefix="ezhrika-alembic-") as directory:
            migration_dir = Path(directory)
            (migration_dir / "versions").mkdir()
            for name in ["env.py", "script.py.mako"]:
                shutil.copyfile(PROJECT_ROOT / "alembic" / name, migration_dir / name)
            shutil.copyfile(
                PROJECT_ROOT / "alembic/versions/0001_initial_schema.py",
                migration_dir / "versions/0001_initial_schema.py",
            )
            with self.engine.begin() as connection:
                config = self.config(connection)
                config.set_main_option("script_location", str(migration_dir))
                config.stdout = io.StringIO()
                command.upgrade(config, "head")
                revision = command.revision(config, message="check template", autogenerate=True)
                ast.parse(Path(revision.path).read_text(encoding="utf-8"))
                command.upgrade(config, "head")
                self.assertEqual(MigrationContext.configure(connection).get_current_revision(), revision.revision)


if __name__ == "__main__":
    unittest.main()
