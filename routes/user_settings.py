# User Settings Routes

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_current_user_id, get_db
from models.db.user_settings import UserSettings
from models.schemas.response import Ok
from models.schemas.user_settings import UserSettingsResponse, UserSettingsUpdate

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/api", tags=["user-settings"])


@router.get("/user-settings", response_model=Ok[UserSettingsResponse])
async def get_user_settings(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found",
        )

    return settings


@router.patch("/user-settings", response_model=Ok[UserSettingsResponse])
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Prepare update dictionary for SQLAlchemy
    update_data: dict[str, Any] = {}

    if settings_update.disable_all_notifications is not None:
        update_data["disable_all_notifications"] = (
            settings_update.disable_all_notifications
        )

    if settings_update.disabled_notification_types is not None:
        update_data["disabled_notification_types"] = (
            settings_update.disabled_notification_types
        )

    if settings_update.task_specific_settings is not None:
        update_data["task_specific_settings"] = settings_update.task_specific_settings

    if settings_update.disable_all_email_notifications is not None:
        update_data["disable_all_email_notifications"] = (
            settings_update.disable_all_email_notifications
        )

    if settings_update.ui_preferences is not None:
        update_data["ui_preferences"] = settings_update.ui_preferences

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update data provided",
        )

    # Perform the update
    result = await db.execute(
        update(UserSettings)
        .where(UserSettings.user_id == user_id)
        .values(**update_data)
        .returning(UserSettings)
    )

    updated_settings = result.scalar_one_or_none()

    if updated_settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found",
        )

    await db.commit()
    return updated_settings
