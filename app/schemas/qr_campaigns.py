from datetime import date
from pydantic import BaseModel

class QrDay(BaseModel):
    day: date
    visits: int

class QrStats(BaseModel):
    campaign: str
    total: int
    today: int
    timezone: str
    days: list[QrDay]
