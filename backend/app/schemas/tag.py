from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    slug: str


class TagUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class TagResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}
