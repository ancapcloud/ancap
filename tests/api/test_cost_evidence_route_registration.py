"""COST-03 route registration: one canonical admin GET, no bare alias."""

from app.main import app


def test_cost_evidence_get_routes_are_canonical_only():
    gets = []
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", "")
        if "GET" in methods and "cost-evidence" in path and "{" in path:
            endpoint = getattr(route, "endpoint", None)
            gets.append(
                (
                    path,
                    f"{endpoint.__module__}.{endpoint.__name__}" if endpoint else None,
                )
            )

    assert gets == [
        (
            "/v1/workflow-store/admin/cost-evidence/{evidence_id}",
            "app.api.routers.workflow_value.get_cost_evidence",
        )
    ]
