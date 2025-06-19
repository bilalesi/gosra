from typing import Any

from pydantic import BaseModel, Field


class UIPreferences(BaseModel):
    theme: str = Field(
        "system",
        description="The UI theme preference.",
        examples=["light", "dark", "system"],
    )
    language: str = Field("en", description="The UI language preference.")
    dashboard_layout: str = Field(
        "compact",
        description="The layout preference for the dashboard.",
        examples=["compact", "comfortable"],
    )


class UserSettingsResponse(BaseModel):
    user_id: str
    disable_all_notifications: bool
    disabled_notification_types: list[str]
    task_specific_settings: dict[str, Any]
    disable_all_email_notifications: bool
    ui_preferences: UIPreferences

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    disable_all_notifications: bool | None = None
    disabled_notification_types: list[str] | None = None
    task_specific_settings: dict[str, Any] | None = None
    disable_all_email_notifications: bool | None = None
    ui_preferences: UIPreferences | None = None
