"""
app — Utility Function Tests
======================================
Tests for helper functions in app/utils.py.
"""

import pytest
from datetime import date, timedelta
from app.utils import calculate_days_left, get_expiry_status


class TestCalculateDaysLeft:
    """Tests for calculate_days_left()."""

    def test_future_date(self):
        """Positive result when expiry is in the future."""
        future = date.today() + timedelta(days=10)
        assert calculate_days_left(future) == 10

    def test_today(self):
        """Zero when expiry is today."""
        assert calculate_days_left(date.today()) == 0

    def test_past_date(self):
        """Negative result when already expired."""
        past = date.today() - timedelta(days=5)
        assert calculate_days_left(past) == -5


class TestGetExpiryStatus:
    """Tests for get_expiry_status()."""

    def test_expired(self):
        assert get_expiry_status(-1) == "Expired"
        assert get_expiry_status(-100) == "Expired"

    def test_expiring_soon(self):
        """0-3 days → Expiring Soon."""
        assert get_expiry_status(0) == "Expiring Soon"
        assert get_expiry_status(1) == "Expiring Soon"
        assert get_expiry_status(3) == "Expiring Soon"

    def test_near_expiry(self):
        """4-7 days → Near Expiry."""
        assert get_expiry_status(4) == "Near Expiry"
        assert get_expiry_status(7) == "Near Expiry"

    def test_safe(self):
        """8+ days → Safe."""
        assert get_expiry_status(8) == "Safe"
        assert get_expiry_status(365) == "Safe"
