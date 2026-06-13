"""Shared parsing helpers."""

import json
import logging

logger = logging.getLogger(__name__)


def parse_hedge_fund_response(response):
    """Parse a JSON string into a dictionary or return None on failure."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as exc:
        logger.error("JSON decoding error: %s | response=%r", exc, response)
        return None
    except TypeError as exc:
        logger.error("Invalid response type (expected string, got %s): %s", type(response).__name__, exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error while parsing response: %s | response=%r", exc, response)
        return None
