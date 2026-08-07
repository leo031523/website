import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.about_content import AboutContent
from app.models.article import Article, ArticleStatus
from app.models.project import Project

from .chunking import chunk_markdown

# MVP 用關鍵字比對做檢索（明確不是語意/向量搜尋，見規格書 9.2 備註）。
_MIN_RELEVANCE_SCORE = 1  # 至少命中一次關鍵字才算相關，未達門檻一律不回傳
_MAX_CHUNKS_PER_SOURCE = 3  # 單一來源最多回傳幾個片段，避免同一篇文章洗版
_SNIPPET_LENGTH = 300
_CJK_RUN_RE = re.compile(r"[一-鿿]+")
_ALNUM_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass
class RetrievedChunk:
    id: str
    title: str
    url: str
    source_type: str
    heading: str | None
    snippet: str
    score: int


def _tokenize(text: str) -> list[str]:
    """中文沒有天然分詞空白，單一中日韓文字當 token 會太沒有辨識度
    ——例如查「字」這種常見單字，幾乎每篇文章都會誤判成相關。改用
    連續中日韓文字的 2-gram（例如「獨特關鍵字」→「獨特」「特關」
    「關鍵」「鍵字」）當作 token，同時保留英數字原本天然的斷詞
    （空白分隔）。這仍然是關鍵字比對，不是語意檢索。"""
    text = text.lower()
    tokens: list[str] = list(_ALNUM_RE.findall(text))
    for run in _CJK_RUN_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def _score(query_tokens: list[str], chunk_text: str) -> int:
    chunk_tokens = _tokenize(chunk_text)
    counts: dict[str, int] = {}
    for t in chunk_tokens:
        counts[t] = counts.get(t, 0) + 1
    return sum(counts.get(qt, 0) for qt in query_tokens)


def _chunks_for_source(
    *,
    content_md: str,
    query_tokens: list[str],
    id_prefix: str,
    title: str,
    url: str,
    source_type: str,
) -> list[RetrievedChunk]:
    results: list[RetrievedChunk] = []
    for chunk in chunk_markdown(content_md):
        score = _score(query_tokens, chunk.text)
        if score < _MIN_RELEVANCE_SCORE:
            continue
        results.append(
            RetrievedChunk(
                id=f"{id_prefix}#chunk-{chunk.index}",
                title=title,
                url=url,
                source_type=source_type,
                heading=chunk.heading,
                snippet=chunk.text[:_SNIPPET_LENGTH],
                score=score,
            )
        )
    results.sort(key=lambda c: c.score, reverse=True)
    return results[:_MAX_CHUNKS_PER_SOURCE]


async def retrieve(db: AsyncSession, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """關鍵字檢索：只從已發布文章、已發布作品與「關於我」內容取材，
    依關鍵字命中次數排序，回傳最相關的前 top_k 個片段。沒有任何內容
    通過最低相關度門檻時回傳空列表——呼叫端應據此判斷是否要讓模型
    明確拒答，而不是硬塞不相關的內容進 prompt。
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    candidates: list[RetrievedChunk] = []

    articles_result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.published)
    )
    for article in articles_result.scalars().all():
        candidates.extend(
            _chunks_for_source(
                content_md=article.content_md,
                query_tokens=query_tokens,
                id_prefix=f"article:{article.id}",
                title=article.title,
                url=f"/blog/{article.slug}",
                source_type="article",
            )
        )

    projects_result = await db.execute(select(Project).where(Project.status == "published"))
    for project in projects_result.scalars().all():
        candidates.extend(
            _chunks_for_source(
                content_md=project.content_md,
                query_tokens=query_tokens,
                id_prefix=f"project:{project.id}",
                title=project.title,
                url=f"/projects/{project.slug}",
                source_type="project",
            )
        )

    about_result = await db.execute(
        select(AboutContent).where(AboutContent.id == AboutContent.SINGLETON_ID)
    )
    about = about_result.scalar_one_or_none()
    if about:
        candidates.extend(
            _chunks_for_source(
                content_md=about.content_md,
                query_tokens=query_tokens,
                id_prefix=f"about:{AboutContent.SINGLETON_ID}",
                title="關於我",
                url="/about",
                source_type="about",
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_k]
