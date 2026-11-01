#!/usr/bin/env python3
"""Load synthetic quality fixtures idempotently; migrations must run first."""
import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.models import QualityFixture
from app.db.session import async_session_maker
from app.schemas.quality_fixtures import QualityFixtureCreate


async def load():
    fixtures_path = Path(__file__).with_name("quality_fixtures_initial.json")
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    rows = [QualityFixtureCreate.model_validate(item).model_dump() for item in fixtures]
    created = 0
    async with async_session_maker() as session:
        async with session.begin():
            for row in rows:
                result = await session.execute(insert(QualityFixture).values(**row).on_conflict_do_nothing(
                    constraint="uq_quality_fixture_sample").returning(QualityFixture.id))
                created += int(result.scalar_one_or_none() is not None)
    print(f"Loaded {created} new synthetic fixtures; {len(rows) - created} already present.")


if __name__ == "__main__":
    asyncio.run(load())
