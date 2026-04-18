"""Tests for credits.py — token math, job slots, upload validation."""

import pytest
import credits as credits_mod
from db import User


class TestRequiredTokens:
    def test_30_seconds(self):
        assert credits_mod.required_tokens(30) == 300

    def test_60_seconds(self):
        assert credits_mod.required_tokens(60) == 600

    def test_fractional_rounds_up(self):
        assert credits_mod.required_tokens(10.1) == 110  # ceil(10.1) * 10

    def test_zero(self):
        assert credits_mod.required_tokens(0) == 0

    def test_one_second(self):
        assert credits_mod.required_tokens(1) == 10


class TestJobSlots:
    def setup_method(self):
        credits_mod._active_jobs.clear()

    def test_acquire_and_release(self):
        assert credits_mod.acquire_job_slot("user1") is True
        assert credits_mod.acquire_job_slot("user1") is False  # already held
        credits_mod.release_job_slot("user1")
        assert credits_mod.acquire_job_slot("user1") is True  # released

    def test_different_users_independent(self):
        assert credits_mod.acquire_job_slot("user1") is True
        assert credits_mod.acquire_job_slot("user2") is True

    def test_release_nonexistent_noop(self):
        credits_mod.release_job_slot("ghost")  # should not raise


class TestValidateUpload:
    def _user(self, balance=1000):
        """Create a lightweight User-like object for validation tests."""
        class FakeUser:
            pass
        u = FakeUser()
        u.credits_balance = balance
        return u

    def test_valid_upload(self):
        err = credits_mod.validate_upload(10 * 1024 * 1024, 30, self._user())
        assert err is None

    def test_file_too_large(self):
        err = credits_mod.validate_upload(100 * 1024 * 1024, 30, self._user())
        assert err is not None
        assert err["error"] == "file_too_large"

    def test_video_too_long(self):
        err = credits_mod.validate_upload(10 * 1024 * 1024, 120, self._user())
        assert err is not None
        assert err["error"] == "video_too_long"

    def test_insufficient_credits(self):
        err = credits_mod.validate_upload(10 * 1024 * 1024, 30, self._user(balance=5))
        assert err is not None
        assert err["error"] == "insufficient_credits"
        assert "offers" in err


class TestTokenModelInfo:
    def test_has_required_keys(self):
        info = credits_mod.token_model_info()
        assert "tokens_per_second" in info
        assert "max_video_seconds" in info
        assert "max_tokens_per_video" in info
        assert info["max_tokens_per_video"] == info["tokens_per_second"] * info["max_video_seconds"]
