"""Guards for the public route surface and metric labels."""

from __future__ import annotations

from types import SimpleNamespace

from app.main import app
from app.services.observability import metric_path_from_scope

ALLOWED_NON_API_PATHS = {
    "/",
    "/docs",
    "/docs/oauth2-redirect",
    "/openapi.json",
    "/redoc",
}


def test_routers_are_mounted_once():
    route_keys = [
        (route.path, tuple(sorted(getattr(route, "methods", None) or ())))
        for route in app.routes
    ]
    assert len(route_keys) == len(set(route_keys)), "duplicate (path, method) route entries"
    assert len(app.routes) < 700, "API surface grew; routers must be mounted once"


def test_api_routes_live_under_v1():
    unexpected = [
        route.path
        for route in app.routes
        if route.path not in ALLOWED_NON_API_PATHS and not route.path.startswith("/v1")
    ]
    assert not unexpected, f"non-canonical API paths: {unexpected[:10]}"


def test_metric_path_prefers_route_template():
    scope = {"route": SimpleNamespace(path="/v1/users/{user_id}"), "path": "/v1/users/123"}
    assert metric_path_from_scope(scope) == "/v1/users/{user_id}"


def test_metric_path_bounds_unmatched_paths():
    assert metric_path_from_scope({"path": "/v1/a/b/c/d"}) == "/v1/a/*"
    assert metric_path_from_scope({"path": "/health"}) == "/health"
