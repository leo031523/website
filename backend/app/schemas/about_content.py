from datetime import datetime

from pydantic import BaseModel


class AboutContentResponse(BaseModel):
    content_md: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class AboutContentUpdate(BaseModel):
    content_md: str
