# schemas/settings_schemas.py
from pydantic import BaseModel
from typing import List


class Setting(BaseModel):
    setting_name: str
    setting_value: str


class SettingsUpdate(BaseModel):
    settings: List[Setting]
