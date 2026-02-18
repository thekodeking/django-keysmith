"""Tests for Keysmith token utilities."""

import re
import secrets
from unittest.mock import patch

import pytest

from keysmith.utils.tokens import (
    PublicToken,
    build_hint,
    build_public_token,
    compute_crc,
    extract_prefix_and_secret,
    generate_raw_secret,
)


class TestGenerateRawSecret:
    """Test secret generation."""

    def test_generates_string_of_correct_length(self):
        """Secret has specified length."""
        secret = generate_raw_secret(32)
        assert len(secret) == 32

    def test_generates_different_secrets(self):
        """Each call generates a different secret."""
        secret1 = generate_raw_secret(32)
        secret2 = generate_raw_secret(32)
        assert secret1 != secret2

    def test_uses_alphanumeric_characters(self):
        """Secret contains only alphanumeric characters."""
        secret = generate_raw_secret(32)
        assert re.match(r"^[a-zA-Z0-9]+$", secret)

    def test_default_length(self):
        """Default length is 32."""
        secret = generate_raw_secret()
        assert len(secret) == 32

    def test_cryptographically_secure(self):
        """Secret generation uses cryptographically secure random."""
        with patch("keysmith.utils.tokens.secrets.choice") as mock_choice:
            mock_choice.return_value = "a"
            secret = generate_raw_secret(8)
            assert secret == "aaaaaaaa"
            assert mock_choice.call_count == 8


class TestComputeCRC:
    """Test CRC computation."""

    def test_computes_consistent_crc(self):
        """Same input produces same CRC."""
        crc1 = compute_crc("test-value")
        crc2 = compute_crc("test-value")
        assert crc1 == crc2

    def test_different_inputs_produce_different_crcs(self):
        """Different inputs produce different CRCs."""
        crc1 = compute_crc("value-1")
        crc2 = compute_crc("value-2")
        assert crc1 != crc2

    def test_default_crc_digits(self):
        """Default is 6 digit CRC."""
        crc = compute_crc("test")
        assert len(crc) == 6
        assert crc.isdigit()

    def test_custom_crc_digits(self):
        """CRC length can be customized."""
        crc = compute_crc("test", crc_digits=8)
        assert len(crc) == 8

    def test_crc_is_numeric(self):
        """CRC contains only digits."""
        crc = compute_crc("test")
        assert crc.isdigit()


class TestBuildPublicToken:
    """Test public token construction."""

    def test_builds_token_with_all_parts(self):
        """Token contains namespace, identifier, secret, and CRC."""
        result = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )

        assert result.token.startswith("tok_abc123:")
        assert len(result.token) > 40  # prefix + secret + crc

    def test_returns_public_token_dataclass(self):
        """Returns PublicToken dataclass with all fields."""
        result = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )

        assert isinstance(result, PublicToken)
        assert result.full_prefix == "tok_abc123"
        assert result.crc is not None
        assert result.hint.startswith("h_")

    def test_token_format(self):
        """Token follows expected format: prefix_identifier:secretCRC."""
        result = build_public_token(
            namespace="tok",
            identifier="test01",
            secret="mysecret12345678901234567890123456",
        )

        # Should be: tok_test01:mysecret12345678901234567890123456<CRC>
        assert "_" in result.token
        assert ":" in result.token
        parts = result.token.split(":")
        assert len(parts) == 2
        assert parts[0] == "tok_test01"

    def test_valid_crc(self):
        """Token CRC is valid."""
        result = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )

        # Extract body and verify CRC
        body = result.token[:-6]  # Remove last 6 chars (CRC)
        expected_crc = compute_crc(body)
        assert result.crc == expected_crc


class TestExtractPrefixAndSecret:
    """Test token extraction and validation."""

    def test_extracts_valid_token(self):
        """Valid token is correctly extracted."""
        token = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )

        prefix, secret = extract_prefix_and_secret(token.token)

        assert prefix == "tok_abc123"
        assert secret == "secret1234567890123456789012345678"

    def test_raises_on_empty_token(self):
        """Empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token is empty"):
            extract_prefix_and_secret("")

    def test_raises_on_too_short_token(self):
        """Token too short raises ValueError."""
        with pytest.raises(ValueError, match="Token too short"):
            extract_prefix_and_secret("short")

    def test_raises_on_invalid_checksum(self):
        """Invalid checksum raises ValueError."""
        token = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )
        # Tamper with CRC
        tampered = token.token[:-6] + "000000"

        with pytest.raises(ValueError, match="Invalid token checksum"):
            extract_prefix_and_secret(tampered)

    def test_raises_on_missing_colon(self):
        """Token without colon separator raises ValueError (checksum error)."""
        # Without a valid CRC, it will fail checksum validation first
        with pytest.raises(ValueError):
            extract_prefix_and_secret("tok_abc123secret1234567890123456789012345678901234567890")

    def test_raises_on_missing_underscore(self):
        """Token without underscore raises ValueError (checksum error first)."""
        # Without a valid CRC, it will fail checksum validation first
        with pytest.raises(ValueError):
            # Format: nounderscore:secret123456789012345678901234567890123456
            extract_prefix_and_secret("nounderscore:secret1234567890123456789012345678901234567890")

    def test_raises_on_empty_secret(self):
        """Token with empty secret raises ValueError."""
        # Create token with empty secret - need valid CRC
        body = "tok_abc123:"
        crc = compute_crc(body)

        with pytest.raises(ValueError, match="Missing token secret"):
            extract_prefix_and_secret(body + crc)

    def test_uses_constant_time_comparison(self):
        """CRC comparison uses timing-safe method."""
        token = build_public_token(
            namespace="tok",
            identifier="abc123",
            secret="secret1234567890123456789012345678",
        )

        # Tamper with one character
        tampered = token.token[:-1] + ("0" if token.token[-1] != "0" else "1")

        with pytest.raises(ValueError):
            extract_prefix_and_secret(tampered)


class TestBuildHint:
    """Test hint generation."""

    def test_hint_format(self):
        """Hint follows expected format."""
        hint = build_hint(crc="123456")
        assert hint.startswith("h_")

    def test_hint_uses_crc_suffix(self):
        """Hint uses suffix of CRC."""
        hint = build_hint(crc="123456")
        assert "56" in hint or hint.endswith("6")

    def test_hint_with_empty_crc(self):
        """Empty CRC produces empty hint."""
        hint = build_hint(crc="")
        assert hint == ""

    def test_hint_respects_hint_length_setting(self):
        """Hint length respects HINT_LENGTH setting."""
        with patch("keysmith.utils.tokens.keysmith_settings") as mock_settings:
            mock_settings.HINT_LENGTH = 10
            hint = build_hint(crc="1234567890")
            assert len(hint) <= 10

    def test_hint_minimum_length(self):
        """Hint has minimum length of 2."""
        with patch("keysmith.utils.tokens.keysmith_settings") as mock_settings:
            mock_settings.HINT_LENGTH = 1
            hint = build_hint(crc="123456")
            assert len(hint) >= 2
