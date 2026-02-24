from app.services.llm_extractor import LLMExtractor


def test_extract_json_with_fenced_block():
    payload = """```json
    {"name":"张三","skills":["python"]}
    ```"""
    data = LLMExtractor._extract_json(payload)
    assert data["name"] == "张三"
    assert data["skills"] == ["python"]
