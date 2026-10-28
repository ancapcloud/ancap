from urllib.parse import urlsplit
"""Quantum-link digital SIM catalog smoke."""


def test_quantum_sim_catalog(client):
    r = client.get("/v1/quantum-sim/catalog")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "quantum" in body["compliance_note"].lower() or "post-quantum" in body["compliance_note"].lower()
    assert len(body["services"]) >= 4
    assert any(s["id"] == "qsim-esim" for s in body["services"])
    assert any(s["id"] == "qsim-global-mesh" for s in body["services"])
    assert urlsplit(body["research_ref"]["url"]).hostname == "www.ixbt.com"
    extra = body.get("research_refs") or []
    assert any(urlsplit(r.get("url") or "").hostname == "naukatv.ru" for r in extra)
    compute = {c["id"] for c in (body.get("compute_stack") or [])}
    assert {"bosonic-codes", "single-period-floquet", "quantum-lattice-gates"} <= compute
    layers = {m["id"] for m in body["mesh_layers"]}
    assert {"satellite", "bts", "repeater"} <= layers
    principles = body.get("principles") or []
    assert len(principles) >= 8
    ids = {p["id"] for p in principles}
    assert {"P1", "P3", "P5", "P8"} <= ids
    assert "0 + 0" in principles[2]["title"] or "superadditivity" in principles[2]["title"].lower()
