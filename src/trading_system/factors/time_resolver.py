import re
from datetime import datetime, timedelta
from typing import Union


class TimeRangeResolver:
    """Resolves relative time range expressions to concrete datetime objects."""

    @staticmethod
    def resolve(expr: str) -> datetime:
        """
        Resolve a time expression to a datetime object.

        Supported formats:
        - 'today' → current date at 00:00:00
        - 'today-Nd' → N days ago at 00:00:00
        - 'today-Nw' → N weeks ago at 00:00:00
        - ISO 8601 string (e.g., '2024-01-01', '2024-01-01T12:00:00')

        Args:
            expr: Time expression string

        Returns:
            datetime object

        Raises:
            ValueError: If expression format is invalid
        """
        expr = expr.strip()

        # Handle 'today' base case
        if expr == 'today':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Handle 'today-Nd' or 'today-Nw' format
        pattern = r'^today-(\d+)([dw])$'
        match = re.match(pattern, expr)
        if match:
            value = int(match.group(1))
            unit = match.group(2)

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if unit == 'd':
                return today - timedelta(days=value)
            elif unit == 'w':
                return today - timedelta(weeks=value)

        # Fallback: try ISO 8601 parsing
        try:
            # Try with time component
            return datetime.fromisoformat(expr)
        except ValueError:
            pass

        try:
            # Try date-only format
            return datetime.strptime(expr, '%Y-%m-%d')
        except ValueError:
            pass

        raise ValueError(f"Invalid time expression: {expr}. "
                        f"Supported formats: 'today', 'today-Nd', 'today-Nw', ISO 8601 strings")
