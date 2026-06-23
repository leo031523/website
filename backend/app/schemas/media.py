from datetime import datetime

from pydantic import BaseModel


class MediaResponse(BaseModel):
    id: int
    filename: str
    url: str
    mime_type: str
    size: int
    alt_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
