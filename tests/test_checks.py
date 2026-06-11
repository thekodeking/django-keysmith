from keysmith.checks import check_keysmith_settings_validity, check_sqlite_concurrency


def test_sqlite_concurrency_check_warns_on_sqlite_default_db():
    """System check emits keysmith.W001 for default sqlite database."""
    warnings = check_sqlite_concurrency(app_configs=None)
    warning = next((item for item in warnings if item.id == "keysmith.W001"), None)

    assert warning is not None
    assert "SELECT FOR UPDATE" in warning.msg
    assert "PostgreSQL" in warning.msg
    assert "MySQL" in warning.msg


def test_keysmith_settings_validity_checks(settings):
    """System check validates config keys, prefix length, secret length, and iterations."""
    # Test valid configuration
    settings.KEYSMITH = {
        "TOKEN_PREFIX": "tok",
        "TOKEN_SECRET_LENGTH": 32,
        "HASH_ITERATIONS": 100_000,
    }
    errors = check_keysmith_settings_validity(app_configs=None)
    assert len(errors) == 0

    # Test invalid configuration: prefix too long
    settings.KEYSMITH = {
        "TOKEN_PREFIX": "a" * 250,
        "TOKEN_SECRET_LENGTH": 32,
        "HASH_ITERATIONS": 100_000,
    }
    errors = check_keysmith_settings_validity(app_configs=None)
    assert any(e.id == "keysmith.E005" for e in errors)

    # Test invalid configuration: secret too short
    settings.KEYSMITH = {
        "TOKEN_PREFIX": "tok",
        "TOKEN_SECRET_LENGTH": 10,
        "HASH_ITERATIONS": 100_000,
    }
    errors = check_keysmith_settings_validity(app_configs=None)
    assert any(e.id == "keysmith.E006" for e in errors)

    # Test invalid configuration: low iterations
    settings.KEYSMITH = {
        "TOKEN_PREFIX": "tok",
        "TOKEN_SECRET_LENGTH": 32,
        "HASH_ITERATIONS": 5_000,
    }
    errors = check_keysmith_settings_validity(app_configs=None)
    assert any(e.id == "keysmith.E007" for e in errors)

    # Test invalid configuration: invalid keys
    settings.KEYSMITH = {
        "TOKEN_PREFIX": "tok",
        "TOKEN_SECRET_LENGTH": 32,
        "HASH_ITERATIONS": 100_000,
        "INVALID_SETTING_KEY": "somevalue",
    }
    errors = check_keysmith_settings_validity(app_configs=None)
    assert any(e.id == "keysmith.W002" for e in errors)
