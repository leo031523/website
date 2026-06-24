from pydantic import BaseModel


class ToolCreate(BaseModel):
    name: str
    category: str | None = None
    url: str | None = None
    icon_url: str | None = None
    description: str | None = None


class ToolUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    url: str | None = None
    icon_url: str | None = None
    description: str | None = None


class ToolResponse(BaseModel):
    id: int
    name: str
    category: str | None
    url: str | None
    icon_url: str | None
    description: str | None

    model_config = {"from_attributes": True}
