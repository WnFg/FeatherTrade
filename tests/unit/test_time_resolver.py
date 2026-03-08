import pytest
from datetime import datetime, timedelta
from src.trading_system.factors.time_resolver import TimeRangeResolver


class TestTimeRangeResolver:
    """Test suite for TimeRangeResolver."""

    def test_resolve_today(self):
        """Test 'today' resolves to current date at 00:00:00."""
        result = TimeRangeResolver.resolve('today')
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        assert result.date() == expected.date()
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_resolve_today_minus_days(self):
        """Test 'today-Nd' format."""
        result = TimeRangeResolver.resolve('today-3d')
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)

        assert result.date() == expected.date()
        assert result.hour == 0

    def test_resolve_today_minus_weeks(self):
        """Test 'today-Nw' format."""
        result = TimeRangeResolver.resolve('today-1w')
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(weeks=1)

        assert result.date() == expected.date()
        assert result.hour == 0

    def test_resolve_iso_date_only(self):
        """Test ISO 8601 date-only format."""
        result = TimeRangeResolver.resolve('2024-03-15')
        expected = datetime(2024, 3, 15)

        assert result == expected

    def test_resolve_iso_datetime(self):
        """Test ISO 8601 datetime format."""
        result = TimeRangeResolver.resolve('2024-03-15T14:30:00')
        expected = datetime(2024, 3, 15, 14, 30, 0)

        assert result == expected

    def test_resolve_invalid_format(self):
        """Test invalid expression raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time expression"):
            TimeRangeResolver.resolve('invalid-format')

    def test_resolve_with_whitespace(self):
        """Test expression with leading/trailing whitespace."""
        result = TimeRangeResolver.resolve('  today-5d  ')
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=5)

        assert result.date() == expected.date()

    def test_resolve_large_offset(self):
        """Test large day offset."""
        result = TimeRangeResolver.resolve('today-365d')
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)

        assert result.date() == expected.date()
