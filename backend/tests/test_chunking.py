from app.services.retrieval.chunking import chunk_markdown


def test_empty_content_produces_no_chunks():
    assert chunk_markdown("") == []
    assert chunk_markdown("   \n  ") == []


def test_short_content_produces_single_chunk():
    chunks = chunk_markdown("這是一段很短的文字。", chunk_size=600, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].text == "這是一段很短的文字。"


def test_long_content_produces_multiple_chunks():
    paragraph = "段落內容 " * 50  # 遠超過 chunk_size
    content = "\n\n".join([paragraph] * 5)
    chunks = chunk_markdown(content, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) > 0


def test_adjacent_chunks_overlap():
    # 用可辨識的獨立單字組成長文，確認相鄰片段之間真的有共同內容，
    # 而不是恰好切在同一個字重複出現的地方。
    words = [f"詞{i:03d}" for i in range(200)]
    content = " ".join(words)
    chunks = chunk_markdown(content, chunk_size=100, overlap=30)
    assert len(chunks) > 1
    for i in range(len(chunks) - 1):
        current_words = set(chunks[i].text.split())
        next_words = set(chunks[i + 1].text.split())
        assert current_words & next_words, "相鄰片段應該共用至少一個詞才算有重疊"


def test_chunks_track_nearest_heading():
    content = (
        "# 標題一\n"
        "這是標題一底下的內容。\n\n"
        "## 標題二\n"
        "這是標題二底下的內容，內容比較長一點。\n"
    )
    chunks = chunk_markdown(content, chunk_size=1000, overlap=0)
    # 內容夠短，通常會被切成一個 chunk，但至少要能抓到「最後一個看到的標題」
    assert any(c.heading in ("標題一", "標題二") for c in chunks)


def test_chunks_before_any_heading_have_no_heading():
    content = "沒有標題的開場白。\n\n# 之後才有標題\n內容。"
    chunks = chunk_markdown(content, chunk_size=10, overlap=0)
    assert chunks[0].heading is None


def test_index_is_sequential():
    paragraph = "重複內容用來確保會被切成很多段落。" * 30
    content = "\n\n".join([paragraph] * 4)
    chunks = chunk_markdown(content, chunk_size=100, overlap=20)
    assert [c.index for c in chunks] == list(range(len(chunks)))
