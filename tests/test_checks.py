from keysmith.checks import check_sqlite_concurrency


def test_sqlite_concurrency_check_warns_on_sqlite_default_db():
    """System check emits keysmith.W001 for default sqlite database."""
    warnings = check_sqlite_concurrency(app_configs=None)
    warning = next((item for item in warnings if item.id == "keysmith.W001"), None)

    assert warning is not None
    assert "SELECT FOR UPDATE" in warning.msg
    assert "PostgreSQL" in warning.msg
    assert "MySQL" in warning.msg
