import threading
from unittest.mock import patch

import pytest

import keysmith.services.tokens
from keysmith.auth.base import authenticate_token
from keysmith.auth.exceptions import InvalidToken, RevokedToken
from keysmith.services.tokens import create_token, revoke_token, rotate_token


@pytest.mark.django_db(transaction=True)
def test_create_token_retries_on_integrity_error():
    """Verify that create_token catches IntegrityError on prefix collision and retries successfully."""
    token1, _ = create_token(name="token-1")

    original_generate_prefix = keysmith.services.tokens._generate_unique_prefix
    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return token1.prefix
        return original_generate_prefix()

    with patch("keysmith.services.tokens._generate_unique_prefix", side_effect=side_effect):
        token2, _ = create_token(name="token-2")

    assert token2.prefix != token1.prefix
    assert call_count == 2


@pytest.mark.django_db(transaction=True)
def test_concurrency_rotate_versus_authentication():
    """Verify concurrent rotation and authentication does not cause database crashes/deadlocks."""
    from django.db import connections
    if connections["default"].vendor == "sqlite":
        pytest.skip("SQLite does not support concurrent write transactions")

    token, raw_token = create_token(name="concurrency-test")
    state = {"exceptions": [], "rotated_raw": raw_token}

    def authenticator():
        for _ in range(50):
            try:
                authenticate_token(state["rotated_raw"])
            except (InvalidToken, RevokedToken):
                # Temporary invalidity during rotation is expected, but not database errors
                pass
            except Exception as e:
                state["exceptions"].append(e)

    def rotator():
        for _ in range(5):
            try:
                state["rotated_raw"] = rotate_token(token)
            except Exception as e:
                state["exceptions"].append(e)

    t1 = threading.Thread(target=authenticator)
    t2 = threading.Thread(target=rotator)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert not state["exceptions"], f"Exceptions raised during concurrent run: {state['exceptions']}"


@pytest.mark.django_db(transaction=True)
def test_concurrency_revoke_versus_authentication():
    """Verify concurrent revoke and authentication does not cause database crashes/deadlocks."""
    from django.db import connections
    if connections["default"].vendor == "sqlite":
        pytest.skip("SQLite does not support concurrent write transactions")

    token, raw_token = create_token(name="concurrency-test-2")
    state = {"exceptions": []}

    def authenticator():
        for _ in range(50):
            try:
                authenticate_token(raw_token)
            except RevokedToken:
                pass
            except Exception as e:
                state["exceptions"].append(e)

    def revoker():
        try:
            revoke_token(token)
        except Exception as e:
            state["exceptions"].append(e)

    t1 = threading.Thread(target=authenticator)
    t2 = threading.Thread(target=revoker)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert not state["exceptions"], f"Exceptions raised during concurrent run: {state['exceptions']}"
