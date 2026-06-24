from pydantic import BaseModel

from app.schemas.article import ArticleListItem
from app.schemas.project import ProjectListItem


class SearchResponse(BaseModel):
    query: str
    articles: list[ArticleListItem]
    projects: list[ProjectListItem]
