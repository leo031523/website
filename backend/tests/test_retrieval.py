import uuid

import pytest
from app.services.retrieval.retriever import retrieve


def _unique_keyword() -> str:
    return f"獨特關鍵字{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_retrieve_finds_published_article(auth_client, cleanup, db_session):
    keyword = _unique_keyword()
    res = auth_client.post(
        "/api/articles",
        json={
            "title": "檢索測試文章",
            "content_md": f"這篇文章的內容包含 {keyword}，用來測試檢索功能是否正常運作。",
            "status": "published",
        },
    )
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])

    results = await retrieve(db_session, keyword, top_k=5)
    assert len(results) == 1
    assert results[0].source_type == "article"
    assert results[0].title == "檢索測試文章"
    assert results[0].url == f"/blog/{article['slug']}"
    assert results[0].id == f"article:{article['id']}#chunk-0"
    assert keyword in results[0].snippet


@pytest.mark.asyncio
async def test_retrieve_excludes_draft_articles(auth_client, cleanup, db_session):
    keyword = _unique_keyword()
    res = auth_client.post(
        "/api/articles",
        json={
            "title": "草稿不應該被檢索到",
            "content_md": f"這篇草稿包含 {keyword}。",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    cleanup("articles", res.json()["id"])

    results = await retrieve(db_session, keyword, top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_retrieve_returns_empty_for_no_match(db_session):
    results = await retrieve(db_session, _unique_keyword(), top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_retrieve_includes_about_content(db_session):
    from app.models.about_content import AboutContent
    from sqlalchemy import select

    result = await db_session.execute(
        select(AboutContent).where(AboutContent.id == AboutContent.SINGLETON_ID)
    )
    about = result.scalar_one()

    # 用「關於我」現有內容裡真的存在的詞來測試，不動它的內容
    results = await retrieve(db_session, "作品集", top_k=5)
    about_hits = [r for r in results if r.source_type == "about"]
    if "作品集" in about.content_md:
        assert about_hits
        assert about_hits[0].url == "/about"


@pytest.mark.asyncio
async def test_retrieve_respects_top_k(auth_client, cleanup, db_session):
    keyword = _unique_keyword()
    for i in range(3):
        res = auth_client.post(
            "/api/articles",
            json={
                "title": f"多篇檢索測試 {i}",
                "content_md": f"內容包含 {keyword} 這個詞。",
                "status": "published",
            },
        )
        assert res.status_code == 201
        cleanup("articles", res.json()["id"])

    results = await retrieve(db_session, keyword, top_k=2)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_retrieve_caps_chunks_per_source(auth_client, cleanup, db_session):
    keyword = _unique_keyword()
    # 用重複段落製造很多命中同一篇文章的 chunk
    paragraph = f"這裡有 {keyword}。" * 5
    content = "\n\n".join([paragraph] * 10)
    res = auth_client.post(
        "/api/articles",
        json={"title": "單篇大量命中測試", "content_md": content, "status": "published"},
    )
    assert res.status_code == 201
    article_id = res.json()["id"]
    cleanup("articles", article_id)

    results = await retrieve(db_session, keyword, top_k=100)
    same_source = [r for r in results if r.id.startswith(f"article:{article_id}#")]
    assert len(same_source) <= 3


@pytest.mark.asyncio
async def test_retrieve_empty_query_returns_empty(db_session):
    results = await retrieve(db_session, "", top_k=5)
    assert results == []
