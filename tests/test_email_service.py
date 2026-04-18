"""Tests for the email_service module."""

import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import email_service


class TestIsConfigured:
  def test_not_configured_by_default(self):
    with patch.dict(os.environ, {"SMTP_HOST": "", "SMTP_USER": "", "SMTP_PASSWORD": ""}, clear=False):
      # Force re-read
      email_service.SMTP_HOST = ""
      email_service.SMTP_USER = ""
      email_service.SMTP_PASSWORD = ""
      assert email_service.is_configured() is False

  def test_configured_when_all_set(self):
    email_service.SMTP_HOST = "smtp.test.com"
    email_service.SMTP_USER = "user"
    email_service.SMTP_PASSWORD = "pass"
    assert email_service.is_configured() is True
    # Reset
    email_service.SMTP_HOST = ""
    email_service.SMTP_USER = ""
    email_service.SMTP_PASSWORD = ""


class TestSendFallback:
  def test_send_returns_false_when_not_configured(self):
    email_service.SMTP_HOST = ""
    result = email_service._send("to@example.com", "Subject", "<p>body</p>")
    assert result is False

  def test_verification_email_logs_url_when_not_configured(self):
    email_service.SMTP_HOST = ""
    result = email_service.send_verification_email("to@test.com", "https://example.com/verify?token=abc")
    assert result is False

  def test_reset_email_logs_url_when_not_configured(self):
    email_service.SMTP_HOST = ""
    result = email_service.send_password_reset_email("to@test.com", "https://example.com/reset?token=abc")
    assert result is False


class TestSendWithSMTP:
  def test_send_success(self):
    email_service.SMTP_HOST = "smtp.test.com"
    email_service.SMTP_USER = "user"
    email_service.SMTP_PASSWORD = "pass"

    with patch("email_service.smtplib.SMTP") as mock_smtp:
      instance = MagicMock()
      mock_smtp.return_value.__enter__ = MagicMock(return_value=instance)
      mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

      result = email_service._send("to@example.com", "Test", "<p>hi</p>")
      assert result is True

    # Reset
    email_service.SMTP_HOST = ""
    email_service.SMTP_USER = ""
    email_service.SMTP_PASSWORD = ""

  def test_send_handles_smtp_error(self):
    email_service.SMTP_HOST = "smtp.test.com"
    email_service.SMTP_USER = "user"
    email_service.SMTP_PASSWORD = "pass"

    with patch("email_service.smtplib.SMTP") as mock_smtp:
      mock_smtp.side_effect = Exception("Connection refused")
      result = email_service._send("to@example.com", "Test", "<p>hi</p>")
      assert result is False

    # Reset
    email_service.SMTP_HOST = ""
    email_service.SMTP_USER = ""
    email_service.SMTP_PASSWORD = ""
