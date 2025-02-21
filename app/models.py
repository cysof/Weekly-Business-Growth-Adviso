from pydantic import BaseModel
from typing import Optional

class BusinessInsight(BaseModel):
    metric: str
    observation: str
    recommendation: str

class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

class TickPayload(BaseModel):
    channel_id: str
    return_url: str
    settings: list[Setting]
