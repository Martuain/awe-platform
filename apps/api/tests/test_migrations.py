from pathlib import Path


def test_alembic_configuration_and_initial_revision_exist():
    root = Path(__file__).parents[1]
    assert (root / "alembic.ini").is_file()
    revision = root / "alembic" / "versions" / "0001_initial_schema.py"
    assert revision.is_file()
    text = revision.read_text()
    assert 'revision = "0001_initial_schema"' in text
    assert "INITIAL_TABLES" in text
    assert "table.create" in text


def test_application_startup_no_longer_creates_schema_directly():
    store = (Path(__file__).parents[1] / "app" / "store.py").read_text()
    start = store.index("async def init_database")
    end = store.index("def build_repository", start)
    block = store[start:end]
    assert "Base.metadata.create_all" not in block
    assert "command.upgrade" in store


def test_execution_state_branch_is_merged_back_to_a_single_head():
    root = Path(__file__).parents[1]
    merge = root / "alembic" / "versions" / "0009_merge_execution_state.py"
    assert merge.is_file()
    text = merge.read_text()
    assert 'revision = "0009_execution_state_merge"' in text
    assert '("0008_website_content", "0002_execution_state")' in text
    # The merge must remain schema-neutral because both branches can already
    # be applied in existing local databases containing customer/test projects.
    upgrade = text.split("def upgrade() -> None:", 1)[1].split("def downgrade() -> None:", 1)[0]
    assert "pass" in upgrade
    assert "create_table" not in upgrade
    assert "drop_table" not in upgrade


def test_cap037_deployment_lifecycle_migration_enforces_currentness():
    root = Path(__file__).parents[1]
    revision = root / "alembic" / "versions" / "0010_deployment_lifecycle.py"
    assert revision.is_file()
    text = revision.read_text()
    assert 'revision = "0010_deployment_lifecycle"' in text
    assert 'sa.Column("lifecycle_role"' in text
    assert 'sa.Column("snapshot_ref"' in text
    assert "ROW_NUMBER() OVER" in text
    assert "uq_website_deployments_one_current" in text
    assert "postgresql_where" in text
    assert "awe-deployment-" in text
