from pydantic import BaseModel, field_validator

from app.schemas.validators import normalize_external_url


class ToolCreate(BaseModel):
    name: str
    category: str | None = None
    url: str | None = None
    icon_url: str | None = None
    description: str | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return normalize_external_url(v)


class ToolUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    url: str | None = None
    icon_url: str | None = None
    description: str | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return normalize_external_url(v)


class ToolResponse(BaseModel):
    id: int
    name: str
    category: str | None
    url: str | None
    icon_url: str | None
    description: str | None

    model_config = {"from_attributes": True}
