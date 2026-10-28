from __future__ import annotations

import argparse
import logging
import asyncio
import random
from dataclasses import dataclass
from typing import Any

import httpx


API_BASE = "http://localhost:8000/v1"


@dataclass
class SimAgent:
    id: str
    roles: list[str]


async def _post(client: httpx.AsyncClient, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
    r = await client.post(f"{API_BASE}{path}", json=json_body)
    r.raise_for_status()
    return r.json()


async def _get(client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    r = await client.get(f"{API_BASE}{path}", params=params)
    r.raise_for_status()
    return r.json()


async def simulate(agents_count: int, steps: int, seed: int) -> None:
    random.seed(seed)
    async with httpx.AsyncClient(timeout=10.0) as client:
        agents: list[SimAgent] = []
        # Create mixed-role agents
        for i in range(agents_count):
            roles = ["seller"] if i % 3 == 0 else ["buyer"] if i % 3 == 1 else ["seller", "buyer"]
            data = await _post(
                client,
                "/agents",
                {
                    "display_name": f"sim_agent_{i}",
                    "public_key": "x" * 32,
                    "roles": roles,
                },
            )
            agents.append(SimAgent(id=data["id"], roles=roles))

        # For simplicity use BaseVertical id from API
        verticals = await _get(client, "/verticals", {"limit": 100})
        base_vertical_id = None
        for v in verticals.get("items") or []:
            if v.get("name") == "BaseVertical":
                base_vertical_id = v["id"]
                break
        if not base_vertical_id:
            raise RuntimeError("BaseVertical not found; run migrations first")

        strategies: list[dict[str, Any]] = []
        listings: list[dict[str, Any]] = []

        for step in range(steps):
            op = random.random()
            if op < 0.25:
                # Create strategy + version + listing for a random seller
                seller_candidates = [a for a in agents if "seller" in a.roles]
                if not seller_candidates:
                    continue
                seller = random.choice(seller_candidates)
                strat = await _post(
                    client,
                    "/strategies",
                    {
                        "name": f"sim_strategy_{step}",
                        "vertical_id": base_vertical_id,
                        "owner_agent_id": seller.id,
                    },
                )
                workflow = {
                    "vertical_id": base_vertical_id,
                    "version": "1.0",
                    "steps": [{"id": "s1", "action": "const", "args": {"value": 1}, "save_as": "x"}],
                }
                ver = await _post(
                    client,
                    f"/strategies/{strat['id']}/versions",
                    {"semver": "1.0.0", "workflow": workflow},
                )
                listing = await _post(
                    client,
                    "/listings",
                    {
                        "strategy_id": strat["id"],
                        "strategy_version_id": ver["id"],
                        "fee_model": {
                            "type": "one_time",
                            "one_time_price": {"amount": "5", "currency": "VUSD"},
                        },
                        "status": "active",
                    },
                )
                strategies.append({"strategy": strat, "version": ver})
                listings.append(listing)
            elif op < 0.6 and listings:
                # Buyer purchases a random listing and may run it
                buyer_candidates = [a for a in agents if "buyer" in a.roles]
                if not buyer_candidates:
                    continue
                buyer = random.choice(buyer_candidates)
                listing = random.choice(listings)
                # Deposit some balance if needed
                try:
                    await _post(
                        client,
                        "/ledger/deposit",
                        {
                            "account_owner_type": "agent",
                            "account_owner_id": buyer.id,
                            "amount": {"amount": "20", "currency": "VUSD"},
                        },
                    )
                except httpx.HTTPStatusError:
                    logging.getLogger(__name__).warning("Simulation deposit failed; continuing without claiming funding")
                try:
                    await _post(
                        client,
                        "/orders",
                        {
                            "listing_id": listing["id"],
                            "buyer_type": "agent",
                            "buyer_id": buyer.id,
                            "payment_method": "ledger",
                        },
                    )
                except httpx.HTTPStatusError:
                    # Self-dealing, quarantine, risk, invariant – treated as simulated abuse
                    continue
                # Try to run once
                pool = await _post(
                    client,
                    "/pools",
                    {"name": f"sim_pool_{step}", "risk_profile": "low"},
                )
                try:
                    await _post(
                        client,
                        "/runs",
                        {
                            "strategy_version_id": listing["strategy_version_id"],
                            "pool_id": pool["id"],
                        },
                    )
                except httpx.HTTPStatusError:
                    # Risk / graph gates etc.
                    continue
            else:
                # Read-only: touch reputation / graph metrics for random agent to exercise jobs & metrics
                agent = random.choice(agents)
                try:
                    await _get(client, f"/agents/{agent.id}/graph-metrics")
                except httpx.HTTPStatusError:
                    continue


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate many agents interacting with the marketplace.")
    parser.add_argument("--agents", type=int, default=50, help="Number of agents to create")
    parser.add_argument("--steps", type=int, default=200, help="Number of random operations to perform")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    asyncio.run(simulate(args.agents, args.steps, args.seed))


if __name__ == "__main__":
    main()

