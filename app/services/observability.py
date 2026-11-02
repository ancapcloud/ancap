from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Mapping
from typing import Any


_lock = threading.Lock()
_http_requests: Counter[tuple[str, str, str]] = Counter()


def metric_path_from_scope(scope: Mapping[str, Any]) -> str:
    """Return a bounded metric label for the matched route.

    Raw request paths contain UUIDs, addresses and slugs; using them as labels
    grows the in-process counter without bound. Prefer the route template
    (``/v1/users/{user_id}``). For unmatched paths keep only the first two
    segments and collapse the rest.
    """
    route = scope.get("route")
    template = getattr(route, "path", None)
    if template:
        return str(template)

    parts = [part for part in str(scope.get("path") or "").split("/") if part]
    if not parts:
        return "/"
    if len(parts) <= 2:
        return "/" + "/".join(parts)
    return "/" + "/".join(parts[:2]) + "/*"


def record_http_request(method: str, path: str, status_code: int) -> None:
    normalized_path = path.split("?")[0]
    with _lock:
        _http_requests[(method.upper(), normalized_path, str(status_code))] += 1


def render_http_metrics() -> str:
    lines = [
        "# HELP ancap_http_requests_total HTTP requests handled by the API process.",
        "# TYPE ancap_http_requests_total counter",
    ]
    with _lock:
        for (method, path, status), count in sorted(_http_requests.items()):
            safe_path = path.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'ancap_http_requests_total{{method="{method}",path="{safe_path}",status="{status}"}} {count}')
    return "\n".join(lines)
