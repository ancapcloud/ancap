from app.db.session import async_session_maker
from app.schemas.workflow_cost_evidence import CostEvidencePublic


async def get_cost_evidence(evidence_id: str) -> CostEvidencePublic | None:
    """Admin endpoint to retrieve cost evidence for verification."""
    async with async_session_maker() as session:
        from app.db.models import CostEvidence
        result = await session.get(CostEvidence, evidence_id)
        if not result:
            return None
        return CostEvidencePublic.model_validate(result)
