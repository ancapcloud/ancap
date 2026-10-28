
from tests.conftest import unique_name


def _create_agent(client, role: str) -> str:
  r = client.post(
    "/v1/agents",
    json={"display_name": unique_name(f"gp_{role}"), "public_key": "x" * 32, "roles": [role]},
  )
  assert r.status_code == 201, r.text
  return r.json()["id"]


def _create_strategy_with_version(client, owner_agent_id: str, base_vertical_id: str) -> tuple[str, str]:
  strat = client.post(
    "/v1/strategies",
    json={
      "name": unique_name("gp_strategy"),
      "vertical_id": base_vertical_id,
      "owner_agent_id": owner_agent_id,
    },
  )
  assert strat.status_code == 201, strat.text
  sid = strat.json()["id"]
  workflow = {
    "vertical_id": base_vertical_id,
    "version": "1.0",
    "steps": [
      {"id": "s1", "action": "const", "args": {"value": 1}, "save_as": "x"},
      {"id": "s2", "action": "math_add", "args": {"a": {"ref": "x"}, "b": 2}},
    ],
  }
  ver = client.post(
    f"/v1/strategies/{sid}/versions",
    json={"semver": "1.0.0", "workflow": workflow},
  )
  assert ver.status_code == 201, ver.text
  vid = ver.json()["id"]
  return sid, vid


def _create_listing(client, strategy_id: str, version_id: str) -> str:
  r = client.post(
    "/v1/listings",
    json={
      "strategy_id": strategy_id,
      "strategy_version_id": version_id,
      "fee_model": {
        "type": "one_time",
        "one_time_price": {"amount": "10", "currency": "VUSD"},
      },
      "status": "active",
    },
  )
  assert r.status_code == 201, r.text
  return r.json()["id"]


def _fund_buyer_ledger(client, buyer_id: str, amount: str = "100", currency: str = "VUSD") -> None:
  r = client.post(
    "/v1/ledger/deposit",
    json={
      "account_owner_type": "agent",
      "account_owner_id": buyer_id,
      "amount": {"amount": amount, "currency": currency},
    },
    headers={"Idempotency-Key": unique_name("idk_deposit")},
  )
  assert r.status_code == 201, r.text


def _get_seller_balance(client, seller_id: str, currency: str = "VUSD") -> float:
  r = client.get("/v1/ledger/balance", params={"owner_type": "agent", "owner_id": seller_id})
  assert r.status_code == 200, r.text
  payload = r.json()
  for item in payload.get("balances") or []:
    if item.get("currency") == currency:
      try:
        return float(item.get("amount") or 0)
      except (TypeError, ValueError):
        return 0.0
  return 0.0


def test_flow1_smoke_golden_path(client, base_vertical_id):
  """Golden Path smoke: seller→listing→buy→grant→run→revenue via HTTP API only."""
  seller_id = _create_agent(client, "seller")
  buyer_id = _create_agent(client, "buyer")

  strategy_id, version_id = _create_strategy_with_version(client, seller_id, base_vertical_id)
  listing_id = _create_listing(client, strategy_id, version_id)

  _fund_buyer_ledger(client, buyer_id, amount="100", currency="VUSD")
  before = _get_seller_balance(client, seller_id, currency="VUSD")

  # Place order with Idempotency-Key
  idk_order = unique_name("idk_order")
  order_body = {
    "listing_id": listing_id,
    "buyer_type": "agent",
    "buyer_id": buyer_id,
    "payment_method": "ledger",
  }
  o1 = client.post("/v1/orders", json=order_body, headers={"Idempotency-Key": idk_order})
  assert o1.status_code == 201, o1.text
  o1j = o1.json()
  assert o1j["status"] == "paid"

  # Grant exists
  grants = client.get(
    "/v1/access/grants",
    params={"limit": 50, "grantee_type": "agent", "grantee_id": buyer_id},
  )
  assert grants.status_code == 200, grants.text
  items = grants.json().get("items") or []
  assert any(g["strategy_id"] == strategy_id and g["scope"] == "execute" for g in items)

  # Create pool and run with Idempotency-Key
  pool = client.post(
    "/v1/pools",
    json={"name": unique_name("gp_pool"), "risk_profile": "experimental"},
  )
  assert pool.status_code == 201, pool.text
  pool_id = pool.json()["id"]

  idk_run = unique_name("idk_run")
  run_body = {
    "strategy_version_id": version_id,
    "pool_id": pool_id,
    "params": {"_start_equity": 1000},
    "limits": {},
    "dry_run": True,
    "run_mode": "mock",
  }
  r1 = client.post("/v1/runs", json=run_body, headers={"Idempotency-Key": idk_run})
  assert r1.status_code == 201, r1.text
  r1j = r1.json()
  assert r1j["state"] in ("running", "succeeded", "completed")

  after = _get_seller_balance(client, seller_id, currency="VUSD")
  # Listing price is 10 VUSD; platform take can leave the seller with 9.5+.
  assert after >= before + 9.5


def test_duplicate_order_same_key_is_idempotent_smoke(client, base_vertical_id):
  seller_id = _create_agent(client, "seller")
  buyer_id = _create_agent(client, "buyer")
  strategy_id, version_id = _create_strategy_with_version(client, seller_id, base_vertical_id)
  listing_id = _create_listing(client, strategy_id, version_id)
  _fund_buyer_ledger(client, buyer_id, amount="100", currency="VUSD")

  idk = unique_name("idk_order")
  body = {
    "listing_id": listing_id,
    "buyer_type": "agent",
    "buyer_id": buyer_id,
    "payment_method": "ledger",
  }
  o1 = client.post("/v1/orders", json=body, headers={"Idempotency-Key": idk})
  assert o1.status_code == 201, o1.text
  o1j = o1.json()

  o2 = client.post("/v1/orders", json=body, headers={"Idempotency-Key": idk})
  assert o2.status_code == 201, o2.text
  o2j = o2.json()
  assert o1j["id"] == o2j["id"]


def test_duplicate_run_same_key_is_idempotent_smoke(client, base_vertical_id):
  seller_id = _create_agent(client, "seller")
  buyer_id = _create_agent(client, "buyer")
  strategy_id, version_id = _create_strategy_with_version(client, seller_id, base_vertical_id)
  listing_id = _create_listing(client, strategy_id, version_id)
  _fund_buyer_ledger(client, buyer_id, amount="100", currency="VUSD")

  idk_order = unique_name("idk_order2")
  client.post(
    "/v1/orders",
    json={"listing_id": listing_id, "buyer_type": "agent", "buyer_id": buyer_id, "payment_method": "ledger"},
    headers={"Idempotency-Key": idk_order},
  )

  pool = client.post(
    "/v1/pools",
    json={"name": unique_name("gp_pool2"), "risk_profile": "experimental"},
  )
  assert pool.status_code == 201, pool.text
  pool_id = pool.json()["id"]

  idk_run = unique_name("idk_run2")
  run_body = {
    "strategy_version_id": version_id,
    "pool_id": pool_id,
    "params": {"_start_equity": 1000},
    "limits": {},
    "dry_run": True,
    "run_mode": "mock",
  }
  r1 = client.post("/v1/runs", json=run_body, headers={"Idempotency-Key": idk_run})
  assert r1.status_code == 201, r1.text
  r1j = r1.json()

  r2 = client.post("/v1/runs", json=run_body, headers={"Idempotency-Key": idk_run})
  assert r2.status_code == 201, r2.text
  r2j = r2.json()
  assert r1j["id"] == r2j["id"]

