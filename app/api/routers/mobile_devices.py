"""Device registration endpoint for mobile push notifications (Phase 6.2).

See docs/mobile/API_MOBILE.md.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession, get_current_user_id
from app.db.models import MobileDevice
from app.schemas.mobile_acp import (
    MobileDeviceInfo,
    MobileDeviceListResponse,
    MobileDeviceRegisterRequest,
    MobileDeviceRegisterResponse,
    MobileDeviceUnregisterRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mobile/devices", tags=["Mobile Devices"])


@router.post("/register", response_model=MobileDeviceRegisterResponse)
async def register_device(
    body: MobileDeviceRegisterRequest,
    session: DbSession,
    user_id: str = Depends(get_current_user_id),
):
    """Register (or update) a device push token for the authenticated user.

    Re-registering the same device_token updates the last_seen_at timestamp
    and re-activates the device if it was previously deactivated.
    """
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    import uuid

    existing = await session.execute(
        __import__("sqlalchemy").select(MobileDevice).where(
            MobileDevice.device_token == body.device_token,
            MobileDevice.user_id == uuid.UUID(user_id),
        )
    )
    device = existing.scalar_one_or_none()

    if device:
        device.is_active = True
        device.platform = body.platform
        device.app_version = body.app_version
        device.last_seen_at = __import__("datetime").datetime.utcnow()
        msg = "Device token updated"
    else:
        device = MobileDevice(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            device_token=body.device_token,
            platform=body.platform,
            app_version=body.app_version,
        )
        session.add(device)
        msg = "Device registered"

    await session.flush()
    logger.info("mobile_device_register: active=%s", bool(device.is_active))

    return MobileDeviceRegisterResponse(device_id=str(device.id), registered=True, message=msg)


@router.post("/unregister")
async def unregister_device(
    body: MobileDeviceUnregisterRequest,
    session: DbSession,
    user_id: str = Depends(get_current_user_id),
):
    """Deactivate a device token (logout / app uninstall)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    import uuid

    row = await session.execute(
        __import__("sqlalchemy").select(MobileDevice).where(
            MobileDevice.device_token == body.device_token,
            MobileDevice.user_id == uuid.UUID(user_id),
        )
    )
    device = row.scalar_one_or_none()
    if device:
        device.is_active = False
        await session.flush()
        logger.info("mobile_device_unregister")
        return {"ok": True, "message": "Device deactivated"}
    return {"ok": True, "message": "Device not found"}


@router.get("", response_model=MobileDeviceListResponse)
async def list_devices(
    session: DbSession,
    user_id: str = Depends(get_current_user_id),
):
    """List all active devices for the authenticated user."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    import uuid
    from sqlalchemy import select

    rows = await session.execute(
        select(MobileDevice).where(MobileDevice.user_id == uuid.UUID(user_id), MobileDevice.is_active == True)
    )
    devices = [
        MobileDeviceInfo(
            device_id=str(d.id),
            platform=d.platform,
            app_version=d.app_version,
            is_active=d.is_active,
            last_seen_at=d.last_seen_at,
            created_at=d.created_at,
        )
        for d in rows.scalars().all()
    ]
    return MobileDeviceListResponse(devices=devices)