"""Report optional failures without exposing provider payloads or credentials."""
import logging

_log = logging.getLogger(__name__)


def report_optional_failure(operation: str, *, quiet: bool = False) -> None:
    """Call with a static operation label; retry decisions remain with its owner."""
    _log.log(logging.DEBUG if quiet else logging.WARNING, "Optional operation failed: %s", operation)
